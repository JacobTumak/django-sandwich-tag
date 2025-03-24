from invoke import Collection

from . import clean, deps, docs, pypi, tox
from .utils import run_act

namespace = Collection(tox, clean, deps, docs, pypi, run_act)