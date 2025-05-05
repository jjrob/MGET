Building MGET's documentation
=============================

MGET uses `Sphinx <https://www.sphinx-doc.org/>`_ to automate the production
of HTML documentation with the `Read the Docs theme
<https://sphinx-rtd-theme.readthedocs.io>`_. After :doc:`building MGET as a
Python wheel <BuildingWheels>` and :doc:`installing it <InstallingWheels>`,
using the same virtual environment you used to build MGET, make sure you're in
the MGET repo's root directory and then execute::

    cd doc/GeoEco
    make html

Assuming no errors occur, the root page of the documentation will be
``_build/html/index.html``. Open it in your browser to view the documentation.

If you make a code change and want to build the documentation again, just run
``make html`` again. This should rebuild only the files necessary to account
for your change. However, Sphinx often cannot determine all of the
documentation files that need to rebuilt, necessitating a rebuild from scratch
in order for your change to be picked up. To rebuild from scratch, first run
``make clean`` prior to running ``make html``.
