import logging
import os
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path

import interruptingcow
import psutil
import pytest
import requests
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, alert_is_present
from selenium.webdriver.support.wait import WebDriverWait
from typing import Callable

JUPYTER_PORT = 10_000
NOTEBOOK_ELEMENT_COUNT = 5  # TODO: We use this to make sure we're loaded- is there a better way?
NOTEBOOKS_PATH = (Path(__file__).parent / "notebooks").absolute()
NOTEBOOK_URL = f"http://localhost:{JUPYTER_PORT}/lab/tree/example_notebook.ipynb"

logger = logging.getLogger('pyquibblerTestLogger')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler("/tmp/test_log.log"))


def kill_process_on(func: Callable):
    for process in psutil.process_iter():
        with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            if func(process):
                process.kill()
            # if '--test-type=webdriver' in process.cmdline():
            #     process.kill()


@pytest.fixture
def driver():
    chrome_options = webdriver.ChromeOptions()
    d = webdriver.Chrome(chrome_options=chrome_options)
    yield d
    kill_process_on(lambda p: '--test-type=webdriver' in p.cmdline())

    d.quit()


@pytest.fixture()
def notebooks_path(tmpdir):
    pyquibbler_tmp_directory = tmpdir.mkdir("pyquibbler")
    tmp_notebooks_path = f"{pyquibbler_tmp_directory}/notebooks"
    shutil.copytree(NOTEBOOKS_PATH, tmp_notebooks_path)
    return tmp_notebooks_path


@pytest.fixture(autouse=True)
def start_jupyter_lab(notebooks_path):
    os.environ["JUPYTER_NOTEBOOK"] = os.path.join(notebooks_path, "example_notebook.ipynb")
    kill_process_on(lambda p: any(c.laddr.port == JUPYTER_PORT for c in p.connections(kind='inet')))

    process = subprocess.Popen([
        "jupyter",
        "lab",
        f"--port",
        str(JUPYTER_PORT),
        "--port-retries",
        "0",
        "--no-browser",
        "--NotebookApp.token=''",
        "--NotebookApp.password=''"
    ], cwd=notebooks_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with interruptingcow.timeout(seconds=5):
        while True:
            try:
                requests.get(NOTEBOOK_URL)
            except requests.ConnectionError:
                pass
            else:
                break
    yield
    process.kill()


@pytest.fixture()
def load_notebook(driver, start_jupyter_lab, notebooks_path):
    driver.get(f"http://localhost:{JUPYTER_PORT}/lab/tree/example_notebook.ipynb")
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CLASS_NAME, "jp-CodeCell")) == NOTEBOOK_ELEMENT_COUNT)


@pytest.fixture()
def assert_no_failures(driver):
    def _assert():
        failed_elements = driver.find_elements(By.CSS_SELECTOR,
                                               value='[data-mime-type="application/vnd.jupyter.stderr"]')
        assert len(failed_elements) == 0
    return _assert


@pytest.fixture()
def click_undo(driver):
    def _click():
        label = driver.find_element(by=By.XPATH,
                                    value='//span[@class="jp-ToolbarButtonComponent-label" and text()="Undo"]')
        label.click()
    return _click


@pytest.fixture()
def run_cells(driver):
    def _run_cell():
        elements = driver.find_elements(by=By.CLASS_NAME, value="jp-CodeCell")

        for element in elements:
            action = webdriver.ActionChains(driver)
            action.move_to_element(element)
            action.click()
            action.key_down(Keys.LEFT_SHIFT).send_keys(Keys.ENTER)
            action.perform()
            WebDriverWait(driver, 5).until(lambda _: element.find_element(By.CSS_SELECTOR,
                                                                          ".jp-InputArea-prompt").text != "[*]:")
    return _run_cell


@pytest.fixture()
def run_code(driver):
    def _run(code):
        driver.execute_async_script(f"""
        const future = Window.pyquibblerKernel.requestExecute({{code: "{code}"}});
        future.onIOPub = (msg) => {{
            if (msg.msg_type == "execute_result") {{
                alert(msg.content.data["text/plain"]);
            }}
        }}
        """)
        alert = WebDriverWait(driver, 3).until(alert_is_present())
        result = alert.text
        alert.accept()
        return result
    return _run


@pytest.fixture()
def add_override(driver):
    def _add(quib_name, left_input_val, right_input_val):
        element = driver.find_element(by=By.XPATH, value=f'//div[text()="{quib_name}"]')
        element.click()

        element = WebDriverWait(driver, 1).until(presence_of_element_located((By.XPATH, '//button[text()="Add Override"]')))
        element.click()

        parent = element.find_element(by=By.XPATH, value="../../..")
        inputs = parent.find_elements(by=By.TAG_NAME, value="input")

        left, right = inputs
        left.send_keys("")
        right.send_keys("")
        left.send_keys(left_input_val)
        right.send_keys(right_input_val)
        right.send_keys(Keys.ENTER)
    return _add


def test_lab_extension_happy_flow(driver, load_notebook, assert_no_failures, run_cells):
    run_cells()

    assert_no_failures()


def test_lab_extension_shows_error_on_undo_with_no_assignments(driver, load_notebook, assert_no_failures,
                                                               click_undo):
    click_undo()

    assert len(driver.find_elements(by=By.CLASS_NAME, value="swal2-container")) > 0

    assert_no_failures()


def test_lab_extension_undo_happy_flow(driver, load_notebook, assert_no_failures,
                                       click_undo, run_cells, run_code, add_override):
    run_cells()
    assert_no_failures()

    raw_default_value = run_code("threshold.get_value()")

    add_override("threshold", "", "5")

    raw_value_after_assignment = run_code("threshold.get_value()")
    # Sanity
    assert raw_value_after_assignment == "5" != raw_default_value

    click_undo()

    raw_value_after_undo = run_code("threshold.get_value()")
    assert raw_value_after_undo == raw_default_value != raw_value_after_assignment
