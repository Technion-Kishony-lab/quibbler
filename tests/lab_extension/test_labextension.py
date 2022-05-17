import logging
import os
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path

import psutil
import pytest
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, alert_is_present
from selenium.webdriver.support.wait import WebDriverWait


JUPYTER_PORT = 10_000
NOTEBOOKS_PATH = (Path(__file__).parent / "notebooks").absolute()

logger = logging.getLogger('pyquibblerTestLogger')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler("/tmp/test_log.log"))


@pytest.fixture
def driver():
    chrome_options = webdriver.ChromeOptions()
    d = webdriver.Chrome(chrome_options=chrome_options)
    yield d

    for process in psutil.process_iter():
        with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            if '--test-type=webdriver' in process.cmdline():
                process.kill()

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

    try:
        # TODO: Why 1? Shouldn't we wait for a log that tells us we're good? Or try accessing the lab
        out, err = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    else:
        if err:
            raise Exception(err)
    yield
    process.kill()


@pytest.fixture()
def load_covid_analysis(driver, start_jupyter_lab, notebooks_path):
    driver.get(f"http://localhost:{JUPYTER_PORT}/lab/tree/example_notebook.ipynb")
    WebDriverWait(driver, 10).until(presence_of_element_located((By.CLASS_NAME, "jp-CodeCell")))


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

        parent = element.find_element(by=By.XPATH, value="..")
        inputs = parent.find_elements(by=By.TAG_NAME, value="input")

        left, right = inputs
        left.send_keys("")
        right.send_keys("")
        left.send_keys(left_input_val)
        right.send_keys(right_input_val)
        right.send_keys(Keys.ENTER)
    return _add


def test_lab_extension_happy_flow(driver, load_covid_analysis, assert_no_failures, run_cells):
    run_cells()

    assert_no_failures()


def test_lab_extension_shows_error_on_undo_with_no_assignments(driver, load_covid_analysis, assert_no_failures,
                                                               click_undo):
    click_undo()

    assert len(driver.find_elements(by=By.CLASS_NAME, value="swal2-container")) > 0

    assert_no_failures()


def test_lab_extension_undo_happy_flow(driver, load_covid_analysis, assert_no_failures,
                                       click_undo, run_cells, run_code, add_override):
    run_cells()
    assert_no_failures()

    raw_default_value = run_code("threshold.get_value()")

    add_override("threshold", "quib", "5")

    raw_value_after_assignment = run_code("threshold.get_value()")
    # Sanity
    assert raw_value_after_assignment == "5" != raw_default_value

    click_undo()

    raw_value_after_undo = run_code("threshold.get_value()")
    assert raw_value_after_undo == raw_default_value != raw_value_after_assignment
