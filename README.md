# Marine Geospatial Ecology Tools (MGET)

Marine Geospatial Ecology Tools (MGET), is a Python package and associated
ArcGIS geoprocessing toolbox produced by the [Marine Geospatial Ecology
Lab](https://mgel.env.duke.edu/) at [Duke University](https://duke.edu/). MGET
provides Python functions and corresponding ArcGIS geoprocessing tools for
working with ecological and oceanographic data.

## Under construction

As of March 2024, we are in the process of porting [MGET
0.8](https://mgel.env.duke.edu/mget/), which is only only available for 32-bit
Python 2.x with ArcGIS 10.x running on Microsoft Windows, to 64-bit Python 3.x
with ArcGIS Pro 3.2 running on Windows and Linux. For now, this repository is
considered unstable and not recommended for use. Please contact [Jason
Roberts](mailto:jason.roberts@duke.edu) to inquire about the project status or
if you have other questions.

## Installation on Windows in the ArcGIS Pro 3.2.2 or later conda environment

ArcGIS Pro utilizes [conda](https://docs.conda.io/) to manage Python packages.
Eventually, we hope to release MGET on
[conda-forge](https://conda-forge.org/), which would allow it to be installed
via conda. Until that time, you can use [pip](https://pypi.org/project/pip/)
to install MGET into an existing ArcGIS Pro conda environment. The practice of
installing packages with pip into conda environments is generally discouraged,
but it does work for MGET.

To get started, you first need to install some packages that MGET needs that
are not provided by ESRI in the default `arcgispro-py3` environment. When we
release MGET as a conda-forge package, conda can take care of these
dependencies automatically, but until then you need to do it yourself. To keep
your conda environment as problem-free as possible, you should use conda
rather than pip to install these, and only use pip to install MGET.

### Step 1. Install micromamba

Unfortunately, ArcGIS Pro 3.2.2 ships with version 4.14.0 of conda, which
predates the [introduction of the libmamba
solver](https://conda.org/blog/2023-07-05-conda-libmamba-solver-rollout/) into
conda. The pre-libmamba solver is notoriously slow, and when we tried to
install one of the packages MGET requires (`copernicusmarine`), it hung with
the message `Solving environment` for a very long time, and then wanted to
upgrade dozens of packages to the latest versions, which was unnecessary and
risky. You can work around this by first installing
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html)
and using it to install dependencies into your conda environment instead of
conda. micromamba is a stand-alone, drop-in replacement for conda that does
not tamper with your conda installation.

1. Start Windows PowerShell.

2. Open micromamba [Automatic
   installation](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#automatic-install)
   in your browser and copy the Windows PowerShell installation expression. It
   begins with `Invoke-Expression`.

3. Paste that into PowerShell and run it. If are asked "Do you want to
   initialize micromamba for the shell activate command?", enter `n` unless
   you know what it means and want to do it. Close PowerShell.

### Step 2. Clone the `arcgispro-py3` environment

We strongly advise you not to install MGET or its dependencies into the
default `arcgispro-py3` environment that ArcGIS Pro creates when it installs.
Instead:

1. Follow [ESRI's
   instructions](https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/clone-an-environment.htm)
   to clone `arcgispro-py3` to a new environment. In these instructions, we'll
   assume it's called `arcgispro-py3-mget`. Alternatively, if you already have
   another environment you wish to use, you can skip this step.

2. [Activate](https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/activate-an-environment.htm)
   the new environment you created, or the existing one you want to use.

### Step 3. Using micromamba, install packages needed by MGET

Thankfully, ESRI preinstalls many packages into the default `arcgispro-py3`
environment, but there are a few we still need:

1. Click Start, open the ArcGIS folder, and start the Python Command Prompt.
   It should show your desired environment as part of the command prompt,
   similar to this:

```
(arcgispro-py3-mget) C:\Users\Jason\AppData\Local\ESRI\conda\envs\arcgispro-py3-mget>
```

2. Run the following command to install the packages:

```
micromamba install --channel conda-forge --yes copernicusmarine docutils python-dotenv scikit-fmm
```

### Step 4. Install MGET with pip

Now we just need to install MGET, which is known as the `mget3` package on
[pipy](https://pypi.org/project/mget3/). If you want pip to download it
automatically from pypi, use the following command. *Important:* Do not remove
the `--no-deps` flag. If you do, pip may fail to recognize that ESRI already
installed the gdal package and pip may try to install gdal itself, which will
fail.

1. From the same Python Command Prompt:

```
python -m pip install --no-deps mget3
```

If you closed the Python Command Prompt in Step 3, just start it again. But
make sure it shows the same environment as you used before
(`arcgispro-py3-mget` in this example). If you want to install MGET from a
wheel (`.whl`) file that you obtained yourself, rather than doing it
automatically from pypi, just replace `mget3` in the command above with the
path to the wheel file.

## Building MGET

If you just want to install and use MGET, you do not need to build it first.
If you wish to build it yourself, [check these instructions](BUILD.md).
