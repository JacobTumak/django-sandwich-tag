from invoke import task
from pathlib import Path


@task(default=True)
def test(c):
    """Run tests in the test-environment."""
    c.run("tox r -m test")


@task(aliases=("cov",))
def coverage(c):
    c.run("tox r coverage")


@task
def static(c):
    """Run all tox environments with a `static` label"""
    c.run("tox r -m static")


@task(aliases=("devenv",))
def venv(c, dir_name=".venv", force=False):
    """
    Initialize the development environment for this project.
    """
    if not force and Path(dir_name).exists():
        choice = input("The directory `.venv` already exists. Would you like to overwrite it? [y/N]\n")
        if choice.lower() != "y":
            return
    c.run(f"tox d -e dev {dir_name}")
