Internal API
============

These classes and functions are considered internal to GeoEco and not
recommended for external use. They are more likely to change than those in the
Public API, and are less well documented.

Metaprogramming
---------------

To facilitate automated exposure of Python methods as ArcGIS geoprocessing
tools, generation of batch processing versions of those methods, validation of
method arguments and property values, and generation of documentation, GeoEco
has a home-grown framework for tagging modules, classes, and methods with type
information and other metadata. We developed this in the 2000s, prior to more
modern initiatives, but it has held up reasonably well for our purposes, so we
haven't sought to update it.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.BatchProcessing
    GeoEco.Dependencies
    GeoEco.Metadata
    GeoEco.Types

Interoperability 
----------------

GeoEco uses these modules to access functionality provided by various major
software frameworks. See also the :mod:`GeoEco.Datasets` module.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.ArcGIS
    GeoEco.Matlab

Utilities 
---------

These utility modules are used across GeoEco's codebase.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.Exceptions
    GeoEco.Logging
