Internal API
============

These classes and functions are considered internal to GeoEco and not
recommended for external use. They are more likely to change than those in the
Public API, and are less well documented.

Module and class metadata
-------------------------

To facilitate automated exposure of Python methods as ArcGIS geoprocessing
tools, validation of method arguments and property values, and generation of
documentation in several formats, we tag many GeoEco modules and classes with
metadata objects.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.Dependencies
    GeoEco.Metadata
    GeoEco.Types

Utilities 
---------

These utility modules are used across GeoEco's codebase.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.Exceptions
    GeoEco.Logging
