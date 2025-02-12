# Marine Geospatial Ecology Tools (MGET)

<img src="https://github.com/jjrob/MGET/blob/main/doc/GeoEco/static/MGET_Logo.png?raw=true" align="right"/>

**MGET**, also known as the **GeoEco** Python library, helps researchers
access, manipulate, and analyze ecological and oceanographic data. MGET can be
accessed through the GeoEco Python API or an associated ArcGIS geoprocessing
toolbox.

MGET was developed by the Duke University [Marine Geospatial Ecology
Lab](https://mgel.env.duke.edu/).

[![Python](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jjrob/95abe8aa003febbd5fcc8308bee55db1/raw/py_badge.json)](https://python.org/) ![Platforms](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jjrob/b59309c5cca46acf1c8d7d56304feac1/raw/plats_badge.json) [![PyPI package](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jjrob/bcc799a93aa3adcf1d234cb1eae659fb/raw/pypi_badge.json)](https://pypi.org/project/mget3/) [![conda-forge package](https://img.shields.io/conda/vn/conda-forge/mget3.svg?style=plastic&logo=condaforge&logoColor=white)](https://anaconda.org/conda-forge/mget3)  
[![Build and test wheels status](https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml/badge.svg)](https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml) [![Data Products tests status](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jjrob/c3761a6823cbf5aaded07b64fa4964b8/raw/badge.json)](https://github.com/jjrob/MGET/actions/workflows/test-data-products.yml) [![Documentation status](https://readthedocs.org/projects/mget/badge/?version=stable&style=plastic)](https://mget.readthedocs.io/en/stable/?badge=stable)

## Installation

MGET requires 64-bit Python 3.9–3.13 running on Windows or Linux. For full
functionality, ArcGIS Pro 3.2.2 or later or ArcGIS Server 11.2 or later is
also required, along with some freely-available software. MGET can be
installed with `pip install mget3`, but please see the platform-specific
instructions below to ensure all prerequisites are met.

* [Windows with ArcGIS Pro or Server](https://mget.readthedocs.io/en/stable/WindowsWithArc.html)
* [Windows without ArcGIS](https://mget.readthedocs.io/en/stable/WindowsWithoutArc.html)
* [Linux with ArcGIS Server](https://mget.readthedocs.io/en/stable/LinuxWithArc.html)
* [Linux without ArcGIS](https://mget.readthedocs.io/en/stable/LinuxWithoutArc.html)
* [Windows with Python 2.x and ArcGIS Desktop (no longer maintained)](https://mget.readthedocs.io/en/stable/WindowsWithArcDesktop.html)

> **Ⓘ Note**
>
> We are still in the process of porting MGET for Python 2.7 and ArcGIS
> Desktop to work with Python 3.x and ArcGIS Pro and Server. Not everything
> has been ported yet. If you have questions about something that is missing,
> please post a question to the [discussion
> forum](https://github.com/jjrob/MGET/discussions).

## Usage Examples

* [GeoEco Python Library](https://mget.readthedocs.io/en/stable/PythonExamples.html)
* [MGET ArcGIS Geoprocessing Toolbox](https://mget.readthedocs.io/en/stable/ArcGISToolboxExamples.html)

## Getting Help and Reporting Bugs

* If you have a question, please post to the [discussion forum](https://github.com/jjrob/MGET/discussions).
* If you find a bug, please [report an issue](https://github.com/jjrob/MGET/issues).

## Citation

MGET was originally documented by the following paper. Although much of the
underlying software architecture has changed since 2010, the overall concept
remains, of using Python to integrate useful code implemented in several
languages and to expose it as an ArcGIS geoprocessing toolbox. If you find
MGET is useful in your work, please cite this paper in your publication. If
you are unable to access the paper, please email jason.roberts@duke.edu for a
copy.

Roberts JJ, Best BD, Dunn DC, Treml EA, Halpin PN (2010) Marine Geospatial
Ecology Tools: An integrated framework for ecological geoprocessing with
ArcGIS, Python, R, MATLAB, and C++. Environmental Modelling & Software
25:1197–1207. doi:
[10.1016/j.envsoft.2010.03.029](https://doi.org/10.1016/j.envsoft.2010.03.029)

## Documentation

* [Public API](https://mget.readthedocs.io/en/stable/PublicAPI.html)
* [Internal API](https://mget.readthedocs.io/en/stable/InternalAPI.html)
* [For MGET Developers](https://mget.readthedocs.io/en/stable/Development.html)
* [Release Notes](https://github.com/jjrob/MGET/blob/main/RELEASE_NOTES.md)

## License

MGET uses the [BSD-3-Clause](https://opensource.org/licenses/bsd-3-clause)
open source software license. MGET incorporates other open source software.
Please see the LICENSE file included with MGET for associated software license
statements for these components. We are grateful to these developers for
making their work freely reusable.
