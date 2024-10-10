Testing MGET
============

MGET relies on the `pytest <https://pytest.org>`__ testing framework to
implement tests that verify that MGET is working as designed. Ultimately, we
aim to use GitHub's automation features to run the tests automatically as part
of a continuous integration process. This is nontrivial, though, because a
number of tests require ArcGIS, which is non-free software that may not be
easily runnable in GitHub's own environment. Until we sort that out, we are
only running tests manually. You should run all tests prior to pushing any
commit to the GitHub repo.


Prepare your Python environment
-------------------------------

After :doc:`building MGET as a Python wheel <BuildingWheels>` and
:doc:`installing it <InstallingWheels>`, you should run the tests from the
same Python virtual environment that you installed MGET into. First, you need
to install the Python packages needed to run pytest. If you have done this
already for this virtual environment, you don't need to do it again. On
Linux::

    python3 -m pip install -U pytest python-dotenv

On Windows, replace ``python3`` with ``python``.

Next, if you have not done so already, create a file ``test/.env`` in your
copy of the MGET repository. This file will contain values of environment
variables needed to log in to remote services that MGET interacts with. Open
the file with your text editor and paste in the following text and replace
``********`` with your own credentials::

    CMEMS_USERNAME=********
    CMEMS_PASSWORD=********
    NASA_EARTHDATA_USERNAME=********
    NASA_EARTHDATA_PASSWORD=********

* ``CMEMS_USERNAME`` and ``CMEMS_PASSWORD`` - your username and password for
  `Copernicus Marine Service <https://marine.copernicus.eu/>`__, a.k.a. CMEMS.

* ``NASA_EARTHDATA_USERNAME`` and ``NASA_EARTHDATA_PASSWORD`` - your username
  and password for `NASA Earthdata
  <https://www.earthdata.nasa.gov/>`__.

.. Warning::
    Your credentials must be entered in plaintext. To keep them secret, be
    careful not to allow anyone else to access this file. Keep the file local
    to your machine. Do not try to commit this file to the repo.
    ``.gitignore`` at the root level of the MGET repository is configured to
    ignore the file if it exists.

If you don't have credentials for a service, delete the lines associated with
that service. MGET's test code will detect that no credentials are available
and skip tests associated with that service.


Run pytest
----------

When you're ready, from the same virtual environment, execute::

    cd test/GeoEco
    pytest

The text scripts will skip relevant tests when needed credentials are not
supplied in the ``.env`` file or certain software is not installed, including:

* ArcGIS Pro
* MATLAB Runtime R2024b or the full version of MATLAB R2024b

Please see the `pytest documentation
<https://docs.pytest.org/en/stable/how-to/usage.html>`__ for instructions on
how to run specific tests and for other information about using pytest.


Writing tests
-------------

Eventually we hope to provide guidance on writing tests for MGET. For now we
only have this placeholder reminding us it needs to be done.
