from invoke import task


def require_docs_enabled(c):
    match c.config.docs.enabled:
        case True:
            return
        case False:
            print(
                "This task requires `docs.enabled` to be set to `True`.",
                "To enable this task, set `docs.enabled: True` in your invoke.yaml file"
            )
        case _:
            print(f"Invalid value for `docs.enabled`.\nExpected `True` or `False`, got: {c.config.docs.enabled}")
    print("Exiting with exit code 1")
    exit(1)


@task
def clean(c):
    """Clean up docs directory"""
    require_docs_enabled(c)
    with c.cd("docs"):
        c.run("make clean")


@task(clean)
def build(c):
    """Clean up and build Sphinx docs"""
    with c.cd("docs"):
        c.run("make html")


@task(build)
def release(c):
    """Push docs to GitHub, triggering webhook to build Read The Docs"""
    c.run("git push")
