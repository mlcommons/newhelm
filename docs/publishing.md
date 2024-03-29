# Publishing
We use [Poetry](https://python-poetry.org/) for publishing NewHELM and its plugins. While we are still in early 
development, we are publishing to a GCP Python Repository located at https://us-central1-python.pkg.dev/ai-safety-dev/aisafety-base-pypi.

Publishing permissions are connected to GCP users and authentication is handled via the gcloud cli. In other words, you
must be successfully logged into a user or service GCP account using [these instructions](https://cloud.google.com/sdk/docs/authorizing) 
that has the appropriate roles and permissions for this project before you are able to publish these packages.

## Configuring Poetry
### Configure the MLCommons base repository as a destination
This will add a destination repository named `mlcommons` to your global Poetry installation.
```shell
poetry config repositories.mlcommons https://us-central1-python.pkg.dev/ai-safety-dev/aisafety-base-pypi
```

### Add keychain authentication for Google Cloud plugin
This will add the appropriate keychain authentication plugin to your global Poetry installation.
```shell
poetry self add keyrings.google-artifactregistry-auth
```

### Add bumpversion plugin
This will add the [poetry-bumpversion](https://github.com/monim67/poetry-bumpversion?tab=readme-ov-file) plugin to your
global Poetry installation.
```shell
poetry self add poetry-bumpversion
```

## Publishing

1. Bump the version of NewHELM and all plugins by using `poetry version <version>`, where `<version>` is one of:
"patch", "minor", or "major". Note that this will bump the versions of all plugins referenced in pyproject.toml
as well.
1. Commit those version changes, make a PR and merge it into main.
1. In Github [create a new release](https://github.com/mlcommons/newhelm/releases/new). Set the tag to be the version number you just created, prefixed by `v`, e.g. `v0.2.1`. Write the release notes. For now, also select "Set as a pre-release".
1. Check out the version of main corresponding to your PR, then use `poetry run python publish_all.py` to automatically build and publish all packages.
