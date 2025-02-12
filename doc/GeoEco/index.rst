.. image:: static/MGET_Logo.png
   :align: right

Marine Geospatial Ecology Tools / GeoEco
========================================

**Marine Geospatial Ecology Tools (MGET)**, also known as the **GeoEco**
Python package, helps researchers access, manipulate, and analyze ecological
and oceanographic data. MGET can be accessed through the GeoEco Python API or
an associated ArcGIS geoprocessing toolbox.

MGET was developed by the Duke University `Marine Geospatial Ecology Lab
<https://mgel.env.duke.edu/>`_.

.. _installing-mget:


Installation
------------

MGET requires 64-bit Python 3.9–3.13 running on Windows or Linux. For full
functionality, ArcGIS Pro 3.2.2 or later or ArcGIS Server 11.2 or later is
also required, along with some freely-available software. MGET can be
installed with ``pip install mget3``, but please the platform-specific
instructions below to ensure all prerequisites are met.

.. toctree::
   :maxdepth: 1
   :caption: Installation
   :hidden:

   WindowsWithArc
   WindowsWithoutArc
   LinuxWithArc
   LinuxWithoutArc
   WindowsWithArcDesktop

- :doc:`WindowsWithArc`
- :doc:`WindowsWithoutArc`
- :doc:`LinuxWithArc`
- :doc:`LinuxWithoutArc`
- :doc:`WindowsWithArcDesktop`

.. Note:: 
   We are still in the process of porting MGET for Python 2.7 and ArcGIS
   Desktop to work with Python 3.x and ArcGIS Pro and Server. Not everything
   has been ported yet. If you have questions about something that is missing,
   please post a question to the `discussion forum
   <https://github.com/jjrob/MGET/discussions>`_.

.. toctree::
   :maxdepth: 1
   :caption: Usage Examples

   PythonExamples
   ArcGISToolboxExamples


Getting Help and Reporting Bugs
-------------------------------

- If you have a question, please `post to the discussion forum <https://github.com/jjrob/MGET/discussions>`_.
- If you find a bug, please `report an issue <https://github.com/jjrob/MGET/issues>`_.


Citation
--------

MGET was originally documented by the following paper. Although much of the underlying software architecture has changed since 2010, the overall concept remains, of using Python to integrate useful code implemented in several languages and to expose it as an ArcGIS geoprocessing toolbox. If you find MGET is useful in your work, please cite this paper in your publication. If you are unable to access the paper, please email jason.roberts@duke.edu for a copy.

Roberts JJ, Best BD, Dunn DC, Treml EA, Halpin PN (2010) Marine Geospatial Ecology Tools: An integrated framework for ecological geoprocessing with ArcGIS, Python, R, MATLAB, and C++. Environmental Modelling & Software 25:1197–1207. doi: `10.1016/j.envsoft.2010.03.029 <https://doi.org/10.1016/j.envsoft.2010.03.029>`_


.. toctree::
   :maxdepth: 2
   :caption: Documentation

   PublicAPI
   InternalAPI
   Development


License
-------

MGET uses the `BSD-3-Clause <https://opensource.org/licenses/bsd-3-clause>`_
open source software license. MGET incorporates other open source software.
Please see the LICENSE file included with MGET for associated software license
statements for these components. We are grateful to these developers for
making their work freely reusable.
