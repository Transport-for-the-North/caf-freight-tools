# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.append("../")

# -- Project information -----------------------------------------------------

project = "Local Freight Tool"
author = "Transport for the North"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "myst_parser",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates", "_templates/autosummary"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Extension Options -------------------------------------------------------

# Change autodoc settings
autodoc_member_order = "groupwise"
autoclass_content = "both"
autodoc_default_options = {
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": False,
    "private-members": False,
    "exclude-members": "__module__, __weakref__, __dict__",
}

# Auto summary options
autosummary_generate = True

modindex_common_prefix = ["LFT."]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

html_show_copyright = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["../images"]

# -- Options for LaTeX output ------------------------------------------------
# Fix the issue with lines of attributes extending off the page
# https://github.com/sphinx-doc/sphinx/issues/7241#issuecomment-595751032
latex_elements = {
    "preamble": r"""
\makeatletter
% \py@argswidth is an available length register, use it rather
% than LaTeX's internal \@tempdima as done abusively by \py@itemnewline
\renewcommand{\pysigline}[1]{%
  \setlength{\py@argswidth}{\dimexpr\labelwidth+\linewidth\relax}%
  \item[{\parbox[t]{\py@argswidth}{\raggedright#1}}]}
\makeatother
"""
}

# Copy README and update image links
original_readme = pathlib.Path("../../README.md")
new_readme = pathlib.Path("_autosummary/README.md")
new_readme.parent.mkdir(exist_ok=True)
with open(original_readme, "rt", encoding="utf-8") as original:
    with open(new_readme, "wt", encoding="utf-8") as new:
        for line in original:
            # Regex for line containing markdown image tag
            pattern = (
                r"^[ \t]*!"  # start of image tag
                r"\[(.*)\]"  # alt text
                r"\((\S*)\s"  # path to image
                r'"(.*)"'  # image caption
                r"\)[ \t]*$"  # end of image tag
            )

            match = re.match(pattern, line)
            if match is None:
                new.write(line)
            else:
                path = match.group(2).replace(r"doc/images", "_static")
                new.write(f'![{match.group(1)}]({path} "{match.group(3)}")\n')
