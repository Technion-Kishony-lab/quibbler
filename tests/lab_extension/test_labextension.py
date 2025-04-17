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
from selenium.webdriver.support import expected_conditions as EC
from typing import Callable

from pyquibbler import Project

JUPYTER_PORT = 10_000
NOTEBOOKS_PATH = (Path(__file__).parent / "notebooks").absolute()
NOTEBOOK_URL = f"http://localhost:{JUPYTER_PORT}/lab/tree/temp_notebook.ipynb"


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
def notebooks_path(tmpdir, request):
    # Use a parameter if provided; otherwise default to 'example_notebook.ipynb'
    notebook_name = getattr(request, "param", "example_notebook.ipynb")

    pyquibbler_tmp_directory = tmpdir.mkdir("pyquibbler")
    temp_notebooks_path = os.path.join(pyquibbler_tmp_directory, "notebooks")
    os.makedirs(temp_notebooks_path, exist_ok=True)

    # Copy the specified notebook to a consistent name for Jupyter to open.
    shutil.copyfile(
        NOTEBOOKS_PATH / notebook_name,
        os.path.join(temp_notebooks_path, "temp_notebook.ipynb")
    )
    return temp_notebooks_path


@pytest.fixture(autouse=True)
def start_jupyter_lab(notebooks_path):
    os.environ["JUPYTER_NOTEBOOK_TEST"] = os.path.join(notebooks_path, "temp_notebook.ipynb")
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
    os.environ.pop("JUPYTER_NOTEBOOK_TEST", None)


@pytest.fixture()
def load_notebook(driver, start_jupyter_lab, notebooks_path):
    driver.get(f"http://localhost:{JUPYTER_PORT}/lab/tree/temp_notebook.ipynb")
    # Wait until the notebook panel is visible, indicating that the notebook has loaded.
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".jp-NotebookPanel")))


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
def click_menu_item(driver):
    def _click(menu_name, item_name, pause=1):
        # Updated XPath: locate the <li> element whose child <div> contains the menu name
        menu_xpath = (
            f'//li[contains(@class, "lm-MenuBar-item") and '
            f'.//div[contains(@class, "lm-MenuBar-itemLabel") and contains(., "{menu_name}")]]'
        )
        menu_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, menu_xpath))
        )
        menu_element.click()

        # Optionally, update the submenu item locator if needed
        item_xpath = f'//li[@role="menuitem"]//div[normalize-space()="{item_name}"]'
        menu_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, item_xpath))
        )
        menu_item.click()
        time.sleep(pause)  # make sure server has time to respond

    return _click


@pytest.fixture()
def clear_output_and_restart_kernel(driver, click_menu_item):
    def _clear_and_restart():
        # Trigger the restart/clear action from the Kernel menu
        click_menu_item('Kernel', 'Restart Kernel and Clear All Outputs' + u'\u2026', 0.1)

        # Try waiting for a dialog using an alternative locator (using a common JupyterLab dialog class)
        confirm_dialog_xpath = '//div[contains(@class, "jp-Dialog")]'
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, confirm_dialog_xpath))
        )

        # Locate and click the confirmation button using a revised locator
        confirm_button_xpath = '//button[contains(., "Restart")]'
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
        )
        confirm_button.click()

    return _clear_and_restart


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
def run_cells(driver, assert_no_failures):
    def _run_cell(should_assert=True):
        elements = driver.find_elements(by=By.CLASS_NAME, value="jp-CodeCell")

        for element in elements:
            action = webdriver.ActionChains(driver)
            action.move_to_element(element)
            action.click()
            action.key_down(Keys.LEFT_SHIFT).send_keys(Keys.ENTER)
            action.perform()
            WebDriverWait(driver, 5).until(lambda _: element.find_element(By.CSS_SELECTOR,
                                                                        ".jp-InputArea-prompt").text != "[*]:")
        if should_assert:
            assert_no_failures()

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


@pytest.mark.parametrize("notebooks_path", ["notebook_with_error.ipynb"], indirect=True)
def test_lab_extension_assert_no_failures_fails(driver, load_notebook, assert_no_failures,
                                                run_cells):
    assert_no_failures()
    with pytest.raises(AssertionError):
        run_cells()


def test_lab_extension_undo_redo_is_initially_disabled(driver, load_notebook, assert_no_failures, is_undo_enabled, is_redo_enabled):
    assert is_undo_enabled() is False
    assert is_redo_enabled() is False

    assert_no_failures()


def test_lab_extension_undo_happy_flow(driver, load_notebook, assert_no_failures,
                                       click_undo, run_cells, run_code, is_undo_enabled, is_redo_enabled):

    Project.get_or_create().clear_undo_and_redo_stacks()

    run_cells()

    raw_default_value = run_code("quib1.get_value()")
    time.sleep(0.1)
    assert is_undo_enabled() is False
    assert is_redo_enabled() is False

    run_code("quib1.assign(5); 'ok'")
    time.sleep(0.1)
    assert is_undo_enabled() is True
    assert is_redo_enabled() is False

    raw_value_after_assignment = run_code("quib1.get_value()")
    # Sanity
    assert raw_value_after_assignment == "5" != raw_default_value
    time.sleep(0.1)
    click_undo()
    plt.pause(0.1)
    assert is_undo_enabled() is False
    assert is_redo_enabled() is True
    time.sleep(0.1)

    raw_value_after_undo = run_code("quib1.get_value()")
    assert raw_value_after_undo == raw_default_value != raw_value_after_assignment


@pytest.mark.parametrize("notebooks_path", ["test_saving.ipynb"], indirect=True)
def test_lab_extension_save_load(driver, load_notebook, assert_no_failures,
        run_cells, run_code, click_menu_item, clear_output_and_restart_kernel):
    run_cells()
    assert eval(run_code('nums.get_value()')) == [1, 2., 3]

    # assign to the quib
    run_code("nums[1] = 5.; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 5., 3]

    # Save the quib assignment to the notebook
    click_menu_item('Quibbler', 'Save Quibs')

    # assign to the quib
    run_code("nums[1] = 6.4; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 6.4, 3]

    # Load the quib assignment from the notebook
    click_menu_item('Quibbler', 'Load Quibs')
    assert eval(run_code('nums.get_value()')) == [1, 5., 3]

    # verify that it still a float
    run_code("nums[1] = 6.4; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 6.4, 3]


@pytest.mark.parametrize("notebooks_path", ["test_saving.ipynb"], indirect=True)
def test_lab_extension_save_save_load(driver, load_notebook, assert_no_failures,
        run_cells, run_code, click_menu_item, clear_output_and_restart_kernel):
    run_cells()
    assert eval(run_code('nums.get_value()')) == [1, 2, 3]

    # assign to the quib and save
    run_code("nums[1] = 4; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 4, 3]
    click_menu_item('Quibbler', 'Save Quibs')

    # assign to the quib and save
    run_code("nums[1] = 5; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 5, 3]
    click_menu_item('Quibbler', 'Save Quibs')

    # assign to the quib
    run_code("nums[1] = 6; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 6, 3]

    # Load the quib assignment from the notebook
    click_menu_item('Quibbler', 'Load Quibs')
    assert eval(run_code('nums.get_value()')) == [1, 5, 3]


@pytest.mark.parametrize("notebooks_path", ["test_saving.ipynb"], indirect=True)
def test_lab_extension_save_load_persist_when_kernel_restarts(driver, load_notebook, assert_no_failures,
        run_cells, run_code, click_menu_item, clear_output_and_restart_kernel):
    run_cells()
    assert eval(run_code('nums.get_value()')) == [1, 2, 3]

    # assign to the quib
    run_code("nums[1] = 5; 'ok'")
    assert eval(run_code('nums.get_value()')) == [1, 5, 3]

    # Save the quib assignment to the notebook
    click_menu_item('Quibbler', 'Save Quibs')

    # Verify the quib assignment is reloaded upon restarting the kernel
    clear_output_and_restart_kernel()
    run_cells()
    assert eval(run_code('nums.get_value()')) == [1, 5, 3]

    # Clear the quib assignment in the notebook
    click_menu_item('Quibbler', 'Clear Quib Data in Notebook')

    # Verify the quib assignment is cleared in the notebook
    clear_output_and_restart_kernel()
    run_cells()
    assert eval(run_code('nums.get_value()')) == [1, 2, 3]
