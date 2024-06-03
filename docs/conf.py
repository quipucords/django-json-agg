"""Sphinx configuration."""

project = "Django JSON Agg"
author = "Discovery Team"
copyright = "2024, Discovery Team"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
