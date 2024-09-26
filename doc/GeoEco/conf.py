# Configuration file for the Sphinx documentation builder for the GeoEco package.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import types

# Hardcoded project information

project = 'GeoEco'
copyright = '2024, Jason J. Roberts'
author = 'Jason J. Roberts'

# Get the version number using setuptools_scm

from setuptools_scm import get_version

version = get_version(os.path.join(os.path.dirname(__file__), '..', '..'))
release = version

# General configuration

extensions = [
    'sphinx.ext.autodoc',           # To document classes, methods, etc. automatically
    'sphinx.ext.napoleon',          # To parse Google-style or numpy-style syntax from docstrings
    'sphinx.ext.autosummary',       # To generate summary tables of classes, methods, etc. and linked pages recursively by wrapping autodoc
    'sphinx.ext.intersphinx',       # To hyperlink types in property, argument, and return values
]

templates_path = ['templates']

exclude_patterns = [
    '_build', 
    'Thumbs.db', 
    '.DS_Store',
]

root_doc = 'index'
show_warning_types = True
highlight_language = 'none'

# Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['static']
html_style = os.path.join('css', 'custom.css')

# autodoc, autosummary, and intersphinx configuration

autoclass_content = 'both'                              # For autoclass directives, concatenate and insert both the class's and the __init__ method's docstrings.
autodoc_default_options = {'show-inheritance': True}    # Display parent classes

autosummary_imported_members = True     # Turn this on so that package __init__.py modules (e.g. GeoEco/Types/__init__.py) can import and re-export names from private submodules (e.g. GeoEco/Types/_Base.py) and have them be documented as if they were part of the package's __init__.py 
autosummary_ignore_module_all = False   # Turn this off so that if a module defines __all__, then autosummary uses it to determine the list of names to document

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'gdal': ('https://gdal.org/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# Define custom roles for linking to ArcGIS arcpy documentation.

import docutils
import sphinx.util.nodes

arcpy_url_formatters = {
    'arcpy': 'https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/%s.htm',
    'arcpy_conversion': 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/conversion/%s.htm',
    'arcpy_management': 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/%s.htm',
    'arcpy_sa': 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/%s.htm',
}

def setup(app):
    for role_name, url_formatter in arcpy_url_formatters.items():
        def arcpy_link_role(name, rawtext, text, lineno, inliner, options={}, content=[], formatter=url_formatter):
            has_explicit, title, target = sphinx.util.nodes.split_explicit_title(text)
            ref = formatter % target.lower()
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=docutils.utils.unescape(title.replace('-','')) + '()', classes=['xref', 'py', 'py-func'])
            return [link_node], []

        role_for_url = types.FunctionType(arcpy_link_role.__code__, arcpy_link_role.__globals__, name=role_name + '_link_role', argdefs=({}, [], url_formatter))
        app.add_role(role_name, role_for_url)
