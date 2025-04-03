# Getting Started

## Development Environment
The `tox.venv` task will initialize a pre-configured virtual environment!

To create the environment, run the invoke task
```bash
inv tox.venv
```

Or run the tox command
```bash
tox d -e dev .venv
```

Either command will create a virtual environment in the project root with all dependencies 
installed.


> If you're using pycharm, make sure to choose the python executable from the created 
environment as your project interpreter in your project settings in pycharm.
> 
> This will likely be `.venv/bin/python3.10` 

---

##  `invoke` Tasks
This project comes with a handful of helpful `invoke` tasks to help simplify and 
normalize your workflow. To see the available tasks, run 
```bash
inv --list
```
from your projects root directory.

The code for these tasks can be found in the `tasks` directory of this project.

>arguments can be passed to the commands run by tox by separating them from the first 
> part of the command using `--`. For example, I could run tests in parallel (using 
> `pytest-xdist`) with
> ```bash
> tox r -e py310 -- -n logical
> ```



## Releasing
To release a new version of this project, run 

```bash
bumpver update --[major|minor|patch] 
```

Bumpver will commit and push a tag matching the version to GitHub, where the 
`.github/workflows/publish.yaml` will publish the new version to `TestPyPI` and `PyPI`

### Alternative methods

Run the invoke task with your token
```bash
inv pypi.release --api-token <api-token> -r pypi
```

Or using your `~/.pypirc` file
```bash
inv pypi.release --use-cfg
```
