import contextlib
import subprocess
import sys
import traceback
from pathlib import Path


HERE = Path(__file__).parent.resolve()


def install_package_from_directory(directory: Path):
    subprocess.check_call([sys.executable, "-m", "pip", "install", '-e', '.'], cwd=str(directory))


@contextlib.contextmanager
def exit_on_fail_with_message(message: str):
    try:
        yield
    except Exception:
        print(traceback.format_exc())
        try:
            import click
            click.echo(click.style(message, fg='red', bold=True))
        except ImportError:
            print(message)
        exit(1)


def install_click_if_necessary():
    print("Checking if click is installed...")
    try:
        import click
    except ImportError:
        print("Click is not installed, installing click...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'click'])
    print()


def is_jupyter_installed():
    try:
        subprocess.check_call(["jupyter", "lab", "path"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return False
    return True


def install_pyquibbler():
    import click
    click.echo("Installing pyquibbler (development)...")
    with exit_on_fail_with_message("Failed to install pyquibbler"):
        install_package_from_directory(HERE / 'pyquibbler')
    click.echo(click.style("\nInstalled pyquibbler!", fg='green', bold=True))


def install_labextension():
    import click
    click.echo("Installing pyquibbler jupyter extension (development)...")
    lab_extension_directory = HERE / 'pyquibbler_labextension'
    with exit_on_fail_with_message("Failed to install pyquibbler jupyter extension"):
        click.echo("-- Running `pip install`...")
        install_package_from_directory(lab_extension_directory)
        click.echo("-- Symlinking jupyter extension...")
        subprocess.check_output(['jupyter', 'labextension', 'develop', '--overwrite', '.'],
                                cwd=str(lab_extension_directory))
        click.echo("-- Building jupyter extension...")
        subprocess.check_output(['jupyter', 'labextension', 'build'],
                                cwd=str(lab_extension_directory))
    click.echo(click.style("\nInstalled pyquibbler lab extension!", fg='green', bold=True))


def run_click_command_line():
    import click

    @click.command()
    def install():
        should_install_extension = False
        if is_jupyter_installed():
            should_install_extension = click.prompt("Would you like to install the Jupyter Lab extension as well? [y/N]",
                                                    type=bool)
        install_pyquibbler()

        if should_install_extension:
            install_labextension()

        click.echo(click.style("\nCompleted installation sucessfully!", fg='green', bold=True))

    click.echo(click.style('Welcome to pyquibbler!\n', fg='green', bold=True))
    install()


if __name__ == '__main__':
    install_click_if_necessary()
    run_click_command_line()
