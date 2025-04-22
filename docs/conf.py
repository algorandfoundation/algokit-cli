# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AlgoKit"
copyright = "2023, Algorand Foundation"
author = "Algorand Foundation"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinx_starlight_builder", "sphinx_markdown_builder"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "cli/index.rst"]

myst_heading_anchors = 4
markdown_http_base = "."
starlight_http_base = "/starlight"

# TODO: Change based on env
# myst_enable_extensions = [
#     "substitution",
# ]
# myst_substitutions = {
#     "README": "",
#     "ARC1": "",
#     "ARC32": "https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0032.md"
# }
