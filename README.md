# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

Bifrost bridge for large-scale transfer of bioimage data using an [OMERO server](https://omero.readthedocs.io/en/stable/). A simplified Python CLI tool and package to transfer image data/metadata from and to an OMERO server.

<br>

---

### Requirements

- Python `3.8`
- typer `0.9.0`
- rich `13.5.2`
- zeroc-ice `3.6.5`
- omero-py `5.13.1` (downgraded from `5.15.0` given ezomero `2.1.0` requirements)
- omero-upload `0.4.0`
- ezomero `2.1.0`


### Install with PyPI

`pip install omero-bifrost`

### Usage

Type `omero-bifrost --help` to see the full range of commands and subcommands.

---

### Development notes

To install packages in `requirements.txt` in the current conda env.:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`

