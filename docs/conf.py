# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AlgoKit"
copyright = "2023, Algorand Foundation"
author = "Algorand Foundation"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_click", "myst_parser", "sphinx_starlight_builder"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
smartquotes = False
