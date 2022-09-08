
import contextlib
import subprocess
import sys
import traceback
from pathlib import Path


HERE = Path(__file__).parent.resolve()


def show_failure_message_and_exist(message: str):
    try:
        import click  # noqa
        click.echo(click.style(message, fg='red', bold=True))
    except ImportError:
        print(message)
    exit(1)


def install_package_from_directory(directory: Path, what):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", '-e', what], cwd=str(directory))
    except subprocess.CalledProcessError as e:
        show_failure_message_and_exist(f'Failed to install. Exception :\n{e}')


@contextlib.contextmanager
def exit_on_fail_with_message(message: str):
    try:
        yield
    except Exception as e:
        print(traceback.format_exc())
        print(f'exception : \n{e}')
        show_failure_message_and_exist(message)


def install_click_if_necessary():
    print("Checking if click is installed...")
    try:
        import click  # noqa
    except ImportError:
        print("Click is not installed, installing click...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'click'])
    print()


def is_jupyter_installed():
    try:
        subprocess.check_call(["jupyter", "lab", "path"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:  # noqa
        return False
    return True


def install_pyquibbler():
    import click  # noqa
    click.echo("Installing pyquibbler (development)...")
    pyquibbler_directory = HERE / 'pyquibbler'
    with exit_on_fail_with_message("Failed to install pyquibbler"):
        install_package_from_directory(pyquibbler_directory, ".[dev, sphinx]")
    click.echo(click.style("\nSuccessfully installed pyquibbler!", fg='green', bold=True))


def install_labextension():
    import click  # noqa
    click.echo("Installing pyquibbler jupyter extension (development)...")
    lab_extension_directory = HERE / 'pyquibbler-labextension'
    with exit_on_fail_with_message("Failed to install pyquibbler jupyter extension"):
        click.echo("-- Running `pip install`...")
        install_package_from_directory(lab_extension_directory, '.')
        click.echo("-- Symlinking jupyter extension...")
        subprocess.check_output(['jupyter', 'labextension', 'develop', '--overwrite', '.'],
                                cwd=str(lab_extension_directory))
        click.echo("-- Building jupyter extension...")
        subprocess.check_output(['jupyter', 'labextension', 'build'],
                                cwd=str(lab_extension_directory))
    click.echo(click.style("\nSuccessfully installed pyquibbler jupyter-lab extension!", fg='green', bold=True))


def run_click_command_line():
    import click  # noqa

    @click.command()
    def install():
        click.echo("Checking if Jupyter lab is installed...")
        if is_jupyter_installed():
            click.echo("Jupyter lab is installed.")
            should_install_extension = click.prompt(
                "Would you like to install also the pyquibbler Jupyter Lab extension? [y/N]",
                type=bool)
        else:
            click.echo("Jupyter lab is not installed.\n"
                       "Continuing installing pyquibbler without the Jupyter Lab extension.")
            should_install_extension = False

        install_pyquibbler()

        if should_install_extension:
            install_labextension()

        click.echo(click.style("\nInstallation completed successfully!", fg='green', bold=True))

    click.echo(click.style('Welcome to pyquibbler!\n', fg='green', bold=True))
    install()


if __name__ == '__main__':
    install_click_if_necessary()
    run_click_command_line()
