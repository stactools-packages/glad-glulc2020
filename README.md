# stactools-glad-glclu2020

[![PyPI](https://img.shields.io/pypi/v/stactools-glad-glclu2020?style=for-the-badge)](https://pypi.org/project/stactools-glad-glclu2020/)
![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/stactools-packages/glad-glclu2020/continuous-integration.yml?style=for-the-badge)

- Name: glad-glclu2020
- Package: `stactools.glad_glclu2020`
- [stactools-glad-glclu2020 on PyPI](https://pypi.org/project/stactools-glad-glclu2020/)
- Owner: @hrodmn
- [Dataset homepage](https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/download.html)
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
  - [item-assets](https://github.com/stac-extensions/item-assets/)
  - [scientific](https://github.com/stac-extensions/scientific/)
  - [version](https://github.com/stac-extensions/version/)
  - [classification](https://github.com/stac-extensions/classification/)
  - [render](https://github.com/stac-extensions/render/)
- Browse the example in human-readable form
  - [`glad-glclu2020-v2`](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/glad-glclu2020/main/examples/glad-glclu2020-v2/collection.json)
  - [`glad-glclu2020-change-v2`](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/glad-glclu2020/main/examples/glad-glclu2020-change-v2/collection.json)
- [Browse a notebook demonstrating the example item and collection](https://github.com/stactools-packages/glad-glclu2020/tree/main/docs/example.ipynb)

A short description of the package and its usage.

## STAC examples

- [Collection](https://github.com/stactools-packages/glad-glclu2020/blob/main/examples/glad-glclu2020-v2/collection.json)
- [Item](https://github.com/stactools-packages/glad-glclu2020/blob/main/examples/glad-glclu2020-v2/2000_40N_080W/2000_40N_080W.json)

## Installation

```shell
pip install stactools-glad-glclu2020
```

## Command-line usage

By default, `stactools-glad-glclu2020` will assume that you are generating STAC metadata for the original files which are stored in a Google storage container and publicly available over HTTP.

```bash
stac gladlclu2020 create-collection \
  --sample-asset-href https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/2000/50N_090W.tif \
  {destination}

stac gladlclu2020 create-item \
  https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/2000/50N_090W.tif \
  {destination}
```

> [!WARNING]  
> These files are not cloud-optimized geotiffs (COGs)!
> Be aware that this has major performance implications for applications that consume the data from these assets.

If you have created your own copy of the data in a different storage container, you can provide a custom URL format for the assets with the `--href-format` parameter in the `create-item` command:

```bash

stac gladlclu2020 create-collection \
  --sample-asset-href {sample_tif_url} \
  {destination}

stac gladlclu2020 create-item \
  --href-format s3://bucket/glad/GLCLU2000-2020/{version}/{year}/{loc}.tif \
  {cog_href} \
  {destination}
```

Use `stac glad-glclu2020 --help` to see all subcommands and options.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
uv venv && uv sync --extra dev
uv run pre-commit install
```

To check all files:

```shell
uv run pre-commit run --all-files
```

To run the tests:

```shell
uv run pytest -vv
```

If you've updated the STAC metadata output, update the examples:

```shell
uv run scripts/update-examples
```
