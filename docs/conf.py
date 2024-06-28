# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import irase_data_manager


sys.path.insert(0, os.path.abspath("../irase_data_manager"))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "i-Rase Data Management"
copyright = "2024, Alejandro Valverde Mahou"
author = "Alejandro Valverde Mahou"
release = irase_data_manager.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]

autodoc_default_options = {
    "member-order": "bysource",
    "special-members": "__init__, __getitem__, __len__, __repr__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
