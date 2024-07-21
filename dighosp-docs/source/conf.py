# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Digital Hospitals \u2014 Internal documentation'
copyright = '2024, Digital Hospitals group, Institute for Manufacturing'
author = 'Yin Chi Chan; Anandarup Mukherjee; Rohit Krishnan'
version = '0.1.0'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinxcontrib.kroki',
    'sphinx_rtd_dark_mode'
]

myst_enable_extensions = [
    "attrs_inline",
    "colon_fence",
    "smartquotes",
    "strikethrough",
    "tasklist",
]


templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_context = {
    'display_github': True,
    'github_user': 'cam-digital-hospitals',
    'github_repo': 'dighosp_monorepo',
    'github_version': 'main',
    'conf_py_path': '/dighosp-docs/source/'
}

html_static_path = ['_static']
html_css_files = ['custom.css']
