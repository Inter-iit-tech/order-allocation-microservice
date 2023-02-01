# OptiServer 🚴🖥️

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library and server application that figures out the best routes for
riders in a last mile delivery warehouse setup. Optimised in accordance to Inter
IIT 2023, Problem Statement 3.

## Setting up 🧑‍💻

To install the required dependencies, follow the steps below:

1.  Clone this repository, and `cd` into it

```shell
git clone https://github.com/rishvic/optirider.git
cd optirider
```

2.  Set up a virtual environment, and activate it

```shell
python -m venv .venv

# 2.1. For *nix (bash/zsh)
source .venv/bin/activate
#  1.2. For Windows (Powershell)
.\.venv\Scripts\activate
```

3.  Install all the dependencies

```shell
pip install -r ./requirements.txt
```

4.  (For development) Install dev dependencies, and set up pre-commit hooks.
    **Note:** Installing the development dependencies will setup [`pre-commit`](https://github.com/pre-commit/pre-commit)
    with the formatter [_Black_](https://github.com/psf/black). What it does is
    check all files for proper formatting before a commit is performed. If it
    finds that any file is improperly formatted, it aborts the commit, and
    formats all improperly formatted files. The changes done by the formatter
    will show up as unstaged changes on top of the staged changes, for the
    developer to add &amp; commit after review. For more information, read the
    [`pre-commit` docs](https://pre-commit.com/index.html) and [_Black_ docs](https://black.readthedocs.io/en/stable/integrations/source_version_control.html#).

```shell
pip install -r ./requirements-dev.txt
pre-commit install
```

## Running 🏃

To run the Django HTTP server, run the following commands:

```shell
# ... assuming that requirements.txt has been installed
# Development server
python manage.py runserver

# Production server, more details on how to deploy linked below:
# https://docs.djangoproject.com/en/4.1/howto/deployment/#how-to-deploy-django
# Eg: Deploying on ASGI using Uvicorn
pip install uvicorn
python -m uvicorn optiserver.asgi:application
```

Note: Before running in a production environment, certain settings need to be
set properly (eg. setting `DEBUG = False`, configuring `ALLOWED_HOSTS` etc.).
For all required production configuration, see the [Deployment Checklist](https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/).

### Configuration Options ⚙️

On top of all the Django server settings, the OptiRider parameters have been set
in the [`settings.py`](optiserver/settings.py), under the dictionary
`OPTIRIDER_SETTINGS` and `OSRM_SETTINGS`, accordingly.

### API 🖧

The server exposes a REST API interface, through which communication is
performed. The server schema should be available on the endpoint
`api/schema/swagger-ui/` or `api/schema/redoc/`. The OpenAPI schema YAML file is
available on `api/schema/`. The YAML schema file can be uploaded &amp; checked
in [Swagger Editor](https://editor.swagger.io) or [ReDoc Interactive Demo](https://redocly.github.io/redoc/).

## TODO 📝

- Add a test module, which will verify that the path given by solver module is feasible.
