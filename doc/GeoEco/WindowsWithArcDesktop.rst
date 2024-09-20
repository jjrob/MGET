Windows with Python 2.x and ArcGIS Desktop (no longer maintained)
=================================================================

.. Important::
    The Python team `sunset Python 2.x
    <https://www.python.org/doc/sunset-python-2/>`_ on January 1, 2020 and the
    last release of Python 2.7 was in April 2020. The last release of ArcGIS
    Desktop (a.k.a. ArcMap) was in December 2021 and ESRI `stopped selling new
    licenses <https://www.esri.com/arcgis-blog/products/arcgis-desktop/announcements/arcmap-enters-mature-support-in-march-2024/>`_
    in July 2024. We cannot continue developing MGET for Python 2.x and ArcGIS
    Desktop now that they have been discontinued. MGET 0.8a79 is the last
    release of MGET for Python 2.x and ArcGIS Desktop.

    We are currently in the process of porting MGET to Python 3.x and ArcGIS
    Pro and we urge you to :doc:`try it instead <WindowsWithArc>`. However, as
    of this writing in September 2024, not all of MGET had been ported yet,
    and we recognize that users may want access to that missing functionality.
    If you wish to continue using MGET 0.8a79 for Python 2.x and ArcGIS
    Desktop, follow installation instructions below.


Prerequisites
-------------

- 32-bit or 64-bit x86 processor (ARM is not currently supported)

- Microsoft Windows XP SP2 or later, or Windows Server 2003 or later

- ArcGIS Desktop 9.1 – 10.8.2


Optional software
-----------------

These are required to run certain parts of MGET. You can wait to install them
later if desired. MGET will report detailed error messages when missing
optional software is needed. Be sure to shut down all ArcGIS programs before
installing them.

- `ArcGIS Spatial Analyst extension <https://www.esri.com/spatialanalyst>`_.
  This is required by a number of MGET tools produce rasters. If your ArcGIS
  license includes this extension but you did not install it, you can re-run
  the ArcGIS setup program to add it to your installation.

- MATLAB Component Runtime (MCR) version 7.7 (free; download `here
  <https://duke.box.com/v/MCRv77Installer>`_) or the full version of MATLAB
  R2007b (not free). Either one is OK. These are required for front detection,
  larval dispersal simulation, and certain interpolation tools. You must
  install these specific versions; others will not work. Multiple versions can
  be installed at the same time, so if you use a different version of MATLAB
  for your own work, you can continue to do so, providing you install MCR 7.7
  or MATLAB R2007b for MGET's use.

- `R statistics program <https://www.r-project.org/>`_ versions 2.5 – 4.1.13.
  MGET 0.8 is only available as a 32-bit program and therefore will not be
  compatible with R 4.2.0 or later, because starting with 4.2.0, R is only
  released as a 64-bit program. If you need to use an MGET 0.8 tool that
  accesses R, we recomend R 4.1.13.

- `NOAA CoastWatch Utilities
  <https://coastwatch.noaa.gov/cwn/data-access-tools/coastwatch-utilities.html>`_,
  version 3.2 or later. These are required if you want to use any of the MGET
  tools that process CoastWatch data. In the CoastWatch Utilities setup, be
  sure to you enable the Command line tools option.


Step 1: Close all ArcGIS applications
-------------------------------------

Close all instances of ArcCatalog, ArcMap, ArcGlobe, etc.


Step 2: If you have ArcGIS 10.1 and earlier, install the latest ArcGIS service pack (optional)
----------------------------------------------------------------------------------------------

You can skip this step if you have ArcGIS 10.2 or later. If you do have ArcGIS
10.1 or earlier, installing the service pack will improve the reliability and
performance of the MGET tools that require ArcGIS.

1. Start **ArcGIS Administrator** (if you have ArcGIS 10.0 and later) or
   **Desktop Administrator** (if you have ArcGIS 9.3.1 and earlier).

2. In the pane on the right side, note the service pack number that appears
   right after the words "ArcGIS Service Pack".

3. Close the Administrator.

4. Open ESRI's `Patches and Service Packs
   <https://support.esri.com/en/downloads/patches-servicepacks/>`_ web page.

5. Find the most recent Service Pack for your version of ArcGIS. If the most
   recent service pack is newer than the one you have installed (or you don’t
   have one installed), download and install it.


Step 3: Install the pywin32 Python package
------------------------------------------

MGET requires that the `pywin32 <https://github.com/mhammond/pywin32>`_ Python
package be installed for your version of Python. Pywin32 is also known as the
*Python Extensions for Windows*. You must install the version of pywin32 that
matches the version of Python that you will be using for MGET. Typically this
is the version of Python that ArcGIS installed for you. If you have ArcGIS
10.1 or later, this is Python 2.7. To download pywin32 for Python 2.7:

- Go to https://github.com/mhammond/pywin32/releases/tag/b228

- Download and install the file that ends with ``.win32-py2.7.exe``.

If you have ArcGIS 10.0 or earlier, you have Python 2.6 or earlier. You must
download this from a different location:

- Go to https://sourceforge.net/projects/pywin32/files/pywin32/

- Search back through the builds, starting with Build 221, until you find a
  file that ends in ``.win32-pyX.Y.exe``, where ``X.Y`` is your Python
  version:

  - ArcGIS Desktop 10.0: Python 2.6
  - ArcGIS Desktop 9.1, 9.3, 9.3.1: Python 2.5
  - ArcGIS Desktop 9.2: Python 2.4

  Download and install that file.


Step 4: If you already have MGET installed, uninstall it
--------------------------------------------------------

1. Bring up the list of installed programs:

   - Windows XP and Server 2003: Start Control Panel, click Add or Remove
     Programs
   - Windows Vista and Server 2008: Start Control Panel, switch to Classic
     View, and click Programs and Features
   - Windows 7, Server 2008 R2: Start Control Panel, view by small icons, and
     click Programs and Features
   - Windows 10: Click Start, click Settings (gear icon), and click Apps

2. Uninstall the program named ``Python X.Y GeoEco-Z`` or ``Python X.Y Marine
   Geospatial Ecology Tools Z``, where ``X.Y`` is your Python version number
   (e.g. ``2.7``) and ``Z`` is an MGET version number (e.g. ``0.8a75``).


Step 5: Download and install MGET 0.8a79
----------------------------------------

Download and install the appropriate MGET setup program from the table below.
The installation program is very simple. Unless you have multiple copies of
Python installed on your machine (which is rare) the setup program has no
options. You can just click **Next** until it completes.

*MGET 0.8a79, released 8 September 2023*

+---------+--------------------------------+-------------------------------------------------------------------------+
| Python  | Compatible with                | Download                                                                |
+---------+--------------------------------+-------------------------------------------------------------------------+
| 2.4 x86 | ArcGIS Desktop 9.2             | `MGET-0.8a79.win32-py2.4.exe <https://duke.box.com/v/mget-08a79-py24>`_ |
+---------+--------------------------------+-------------------------------------------------------------------------+
| 2.5 x86 | ArcGIS Desktop 9.1, 9.3, 9.3.1 | `MGET-0.8a79.win32-py2.5.exe <https://duke.box.com/v/mget-08a79-py25>`_ |
+---------+--------------------------------+-------------------------------------------------------------------------+
| 2.6 x86 | ArcGIS Desktop 10.0            | `MGET-0.8a79.win32-py2.6.exe <https://duke.box.com/v/mget-08a79-py26>`_ |
+---------+--------------------------------+-------------------------------------------------------------------------+
| 2.7 x86 | ArcGIS Desktop 10.1-10.8.2     | `MGET-0.8a79.win32-py2.7.exe <https://duke.box.com/v/mget-08a79-py27>`_ |
+---------+--------------------------------+-------------------------------------------------------------------------+


Step 6: Add MGET to your default ArcToolbox window
--------------------------------------------------

The MGET setup program does this automatically for the user that installed
MGET. But other users must add the toolbox manually. This is usually necessary
on classroom computers and similar machines that are accessed by multiple
users.

To manually add the toolbox for your user account:

1. Close all ArcGIS applications (ArcMap, ArcCatalog, ArcGlobe, etc.).

2. Start ArcCatalog.

3. If the ArcToolbox window is not visible, click the red ArcToolbox button to
   bring it up

4. If you don't see **Marine Geospatial Ecology Tools** listed in the
   ArcToolbox window, right click on ArcToolbox and select **Add Toolbox**.

5. Navigate to ``C:\Program Files\GeoEco\ArcGISToolbox`` and add the toolbox
   you see there. You should now see MGET in the ArcToolbox window.

6. Close ArcCatalog.

From now on, MGET will appear in the ArcToolbox window of ArcCatalog and all
new ArcMap documents (``.mxd`` files).

For *existing* ArcMap documents, you must add the toolbox manually within
ArcMap for that document: Start ArcMap, open the document, and follow steps
4-6 above. This is necessary because each ArcMap document maintains a
customized ArcToolbox list. The list is initialized to a copy of ArcCatalog’s
list whenever a new map is created, but exists independently from that point
forward.

.. Note::
    Because MGET 0.8 is only available for 32-bit Python, even when running on
    a 64-bit processor, MGET 0.8 will only work with ArcGIS Desktop (i.e., the
    32-bit ArcMap and ArcCatalog applications). It will not work with ArcGIS
    `64-Bit Background Geoprocessing
    <https://desktop.arcgis.com/en/arcmap/latest/analyze/executing-tools/64bit-background.htm>`_.
    When you run MGET tools, be sure to run them in foreground mode.


MGET 0.8 Copyright and License
------------------------------

Except where otherwise noted, Marine Geospatial Ecology Tools 0.8 and prior
releases are Copyright © 2008–2023 by Jason J. Roberts. MGET is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version. MGET is distributed in
the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
the GNU General Public License (available in the file LICENSE.txt in MGET's
installation directory) for more details.
