import os
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path

import matplotlib.pyplot as plt
import psutil
import pytest
import requests
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, alert_is_present
from selenium.webdriver.support.wait import WebDriverWait
from typing import Callable

from pyquibbler import Project

JUPYTER_PORT = 10_000
NOTEBOOK_ELEMENT_COUNT = 5  # TODO: We use this to make sure we're loaded- is there a better way?
NOTEBOOKS_PATH = (Path(__file__).parent / "notebooks").absolute()
NOTEBOOK_URL = f"http://localhost:{JUPYTER_PORT}/lab/tree/example_notebook.ipynb"


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
    d = webdriver.Chrome(options=chrome_options)
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

    for try_number in range(10):
        try:
            requests.get(NOTEBOOK_URL)
        except requests.ConnectionError:
            time.sleep(0.5)
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
def is_undo_enabled(driver):
    def _is_enabled():
        label = driver.find_element(by=By.XPATH,
                                    value='//span[@class="jp-ToolbarButtonComponent-label" and text()="Undo"]')
        button = label.find_element(By.XPATH, "./..").find_element(By.XPATH, "./..")
        return button.is_enabled()

    return _is_enabled


@pytest.fixture()
def is_redo_enabled(driver):
    def _is_enabled():
        label = driver.find_element(by=By.XPATH,
                                    value='//span[@class="jp-ToolbarButtonComponent-label" and text()="Redo"]')
        button = label.find_element(By.XPATH, "./..").find_element(By.XPATH, "./..")
        return button.is_enabled()

    return _is_enabled


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


def test_lab_extension_happy_flow(driver, load_notebook, assert_no_failures, run_cells):
    run_cells()

    assert_no_failures()


def test_lab_extension_undo__redo_is_initially_disabled(driver, load_notebook, assert_no_failures, is_undo_enabled, is_redo_enabled):
    assert is_undo_enabled() is False
    assert is_redo_enabled() is False

    assert_no_failures()


def test_lab_extension_undo_happy_flow(driver, load_notebook, assert_no_failures,
                                       click_undo, run_cells, run_code, is_undo_enabled, is_redo_enabled):

    Project.get_or_create().clear_undo_and_redo_stacks()

    run_cells()
    assert_no_failures()

    raw_default_value = run_code("threshold.get_value()")

    assert is_undo_enabled() is False
    assert is_redo_enabled() is False

    run_code("threshold.assign(5); 'ok'")

    assert is_undo_enabled() is True
    assert is_redo_enabled() is False

    raw_value_after_assignment = run_code("threshold.get_value()")
    # Sanity
    assert raw_value_after_assignment == "5" != raw_default_value

    click_undo()
    plt.pause(0.1)
    assert is_undo_enabled() is False
    assert is_redo_enabled() is True

    raw_value_after_undo = run_code("threshold.get_value()")
    assert raw_value_after_undo == raw_default_value != raw_value_after_assignment
