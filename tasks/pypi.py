from invoke import task

from . import clean as clean_task
from . import docs as docs_task


@task
def clean(c):
    """Clean up dist (and docs if enabled) directory"""
    c.run("rm -fr ./dist/*")
    if bool(c.config.docs.enabled):
        docs_task.clean(c)


@task(pre=[clean])
def build(c):
    """Clean up and build a new distribution. Builds docs if enabled."""
    if bool(c.config.docs.enabled):
        docs_task.build(c)
    c.run("python3 -m build")


@task
def get_version(c):
    """Return current version using bumpver"""
    c.run("bumpver show --no-fetch")


@task(
    help={
        "api-token": "Obtain an API key from https://pypi.org/manage/account/",
        "repo": "Specify:  pypi  for a production release.",
    }
)
def upload(c, api_token=None, repo="testpypi", use_cfg=False, verbose=False):
    """Upload build to given PyPI repo"""
    vb = "--verbose" if verbose else ""
    if use_cfg is True:
        c.run(f"twine upload --config-file ~/.pypirc --repository {repo} dist/* {vb}")
    else:
        c.run(f"twine upload --repository {repo} -u __token__ -p {api_token} dist/* {vb}")


@task(help={"dist": "Name of distribution file under dist/ directory to check."})
def check(c, dist):
    """Twine check the given distribution"""
    c.run(f"twine check dist/{dist}")


@task(
    pre=[clean],
    post=[clean_task.clean_all],
    help={
        "api-token": "Obtain an API key from https://pypi.org/manage/account/",
        "repo": "Specify:  pypi  for a production release.",
    },
)
def release(c, api_token, repo="testpypi"):
    """Build release and upload to PyPI"""
    print("Fetching version...")
    get_version(c)
    if input("Continue? (y/n): ").lower()[0] != "y":
        print("Release aborted.")
        exit(0)
    print("Building new release...")
    build(c)
    print(f"Uploading release to {repo}...")
    upload(c, repo)
    print("Success! Your package has been released.")
