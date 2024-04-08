# Configuration file for the Sphinx documentation builder for the GeoEco package.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GeoEco'
copyright = '2024, Jason J. Roberts'
author = 'Jason J. Roberts'

# Get the version number using setuptools_scm

from setuptools_scm import get_version

release = get_version(os.path.join(os.path.dirname(__file__), '..', '..'))
version = ".".join(release.split('.')[:3])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_style = os.path.join('css', 'custom.css')
