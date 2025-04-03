# Django Sandwich Tags

**A django template tag that simplifies nested templates.**

---
[![PyPI Version](https://img.shields.io/pypi/v/django-sandwich-tag.svg)](https://pypi.python.org/pypi/django-sandwich-tag)
[![Tests](https://github.com/jacobtumak/django-sandwich-tag/.github/workflows/pytest.yaml/badge.svg)](https://github.com/jacobtumak/django-sandwich-tag/.github/workflows/pytest.yaml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/jacobtumak/sandwich)

Version: 0.1.3

## Overview

The `sandwich` template tag is a Django template tag that allows for easy composition of templates by wrapping a child template inside a parent template. This is particularly useful when building reusable UI components where a consistent layout needs to be enforced while allowing for dynamic content injection. It complements Django's built-in template inheritance by enabling support for nestable, reusable templates and components, rather than replacing it.

## Installation

To use the `sandwich` template tag in your Django project, install the package and add it to your Django app's template tag modules.

1. Ensure your Django project is set up and running.
2. Add the `sandwich_tag` module to one of your installed Django apps.
3. Load the template tag in your Django template:

```django
{% load sandwich %}
```

## Usage

### Basic Example

The `sandwich` template tag is used to wrap a block of content inside a parent template. The child content will be injected into the parent template at the placeholder `{{ sandwich_fixings }}`.

#### Example Parent Template (`card_component.html`):

```html
<div class="card">
    <div class="card-header">
        <h2>{{ title }}</h2>
    </div>
    <div class="card-body">
        {{ sandwich_fixings }}
    </div>
</div>
```

#### Example Usage in Another Template:

```django
{% sandwich "card_component.html" title="Welcome" %}
    <p>This content will be wrapped inside a card component.</p>
{% endsandwich %}
```

### Passing Additional Context

Additional key-value pairs can be passed to the `sandwich` tag, which will be available in the parent template:

```django
{% sandwich "card_component.html" title="User Info" theme="dark" %}
    <p>This content inherits the "theme" variable.</p>
{% endsandwich %}
```

### Using a Template Object Instead of a String

You can also pass a `Template` object instead of a template filename:

```django
{% sandwich some_template_object title="Dynamic Title" %}
    <p>Using a template object dynamically.</p>
{% endsandwich %}
```

## How It Works

1. The `sandwich` tag takes a required `template` argument, which specifies the parent template.
2. The child block content is rendered separately and passed as `sandwich_fixings`.
3. The parent template is rendered with any additional key-value arguments provided.

## Complements Django's Template Inheritance

Django's template inheritance system is great for structuring large applications, but it lacks a built-in way to create deeply nestable, reusable templates or UI components. `sandwich` fills this gap by allowing content blocks to be dynamically wrapped in different parent templates while maintaining flexibility in context passing. This makes it an excellent tool for building modular front-end structures in Django applications.

## Error Handling

- If the `template` argument is missing, a `TemplateSyntaxError` is raised.
- If `template` is provided both as a positional and keyword argument, an error is raised.
- If `template` is not a string or a `Template` object, an error is raised.

## License

This package is released under the MIT License.

---

Enjoy building templates with `sandwich`! 🥪




## Quick Start

1. Install the `sandwich` package from PyPI
    ```bash
    $ pip install sandwich
    ```

2. Add `'sandwich'` to `INSTALLED_APPS`:
    ```python
    INSTALLED_APPS = [
        ...,
        "sandwich",
           ...,
    ]
    ```
   
## Get Me Some of That
* [Source Code](https://github.com/jacobtumak/sandwich)

* [Issues](https://github.com/jacobtumak/sandwich/issues)
* [PyPI](https://pypi.org/project/sandwich)

[MIT License](https://github.com/jacobtumak/sandwich/blob/master/LICENSE)


### Acknowledgments
This project would be impossible to maintain without the help of our generous [contributors](https://github.com/jacobtumak/sandwich/graphs/contributors)

#### Technology Colophon

Without django and the django dev team, the universe would have fewer rainbows and ponies.

This package was originally created with [`cookiecutter`](https://www.cookiecutter.io/) 
and the [`cookiecutter-powder-pypackage`](https://github.com/JacobTumak/CookiePowder) project template.


## For Developers
Initialise the development environment using the invoke task
   ```bash
   inv tox.venv
   ```
Or create it with tox directly
   ```bash
   tox d -e dev .venv
   ```
Or install the dev requirements with pip
   ```bash
   pip install -r reqirements_dev.txt
   ```

### Tests
   ```bash
   pytest
   ```
or
   ```bash
   tox r
   ```
or run tox environments in parallel using
   ```bash
   tox p
   ```

### Code Style / Linting
   ```bash
   $ isort
   $ black
   $ flake8
   ```

### Versioning
 * [Semantic Versioning](https://semver.org/)
   ```bash
   $ bumpver show
   ```



### Build / Deploy Automation
 * [invoke](https://www.pyinvoke.org/)
   ```bash
   $ invoke -l
   ```
 * [GitHub Actions](https://docs.github.com/en/actions) (see [.github/workflows](https://github.com/jacobtumak/sandwich/tree/master/.github/workflows))
 * [GitHub Webhooks](https://docs.github.com/en/webhooks)  (see [settings/hooks](https://github.com/jacobtumak/sandwich/settings/hooks))
