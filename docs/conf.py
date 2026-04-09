# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
from pathlib import Path

# -- Project information -------------------------------------------------------

# Read version from VERSION.txt at the repository root.
_version_file = Path(__file__).parent.parent / "VERSION.txt"
_version = _version_file.read_text().strip() if _version_file.exists() else "1.0.0"

project = "GeoPeriX"
copyright = "2024, GeoPeriX Developers"
author = "GeoPeriX Developers"
version = _version          # short X.Y
release = _version          # full X.Y.Z

# -- General configuration -----------------------------------------------------

extensions = [
    "myst_parser",              # Markdown source files
    "sphinx_copybutton",        # Copy buttons on code blocks
    "sphinx.ext.autosectionlabel",  # Cross-reference sections by title
    "sphinx.ext.intersphinx",   # Link to other projects' documentation
    "sphinx.ext.viewcode",      # Source links in API pages
]

# -- MyST configuration --------------------------------------------------------
# Allow MyST to parse all .md files and enable useful extensions.

myst_enable_extensions = [
    "colon_fence",      # ::: directive syntax (alternative to ```)
    "deflist",          # Definition lists
    "fieldlist",        # reStructuredText-style field lists inside Markdown
    "substitution",     # |replace| substitutions
    "tasklist",         # - [ ] task lists
    "attrs_inline",     # Inline attribute syntax {.class #id}
    "smartquotes",      # Curly quotes
    "linkify",          # Auto-link bare URLs
]

myst_heading_anchors = 3        # Generate anchors for H1–H3
myst_substitutions = {
    "version": release,
    "project": project,
}

# Source suffix: accept both .rst and .md
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst",
}

# Root document
root_doc = "index"

# Patterns to exclude from the build
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML output ---------------------------------------------------------------

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "navbar_start":  ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end":    ["navbar-icon-links", "theme-switcher"],
    "icon_links": [
        {
            "name": "GitHub",
            "url":  "https://github.com/smartgeotechnics/GeoPeriX",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url":  "https://pypi.org/project/geoperix/",
            "icon": "fa-brands fa-python",
        },
    ],
    "logo": {
        "text": f"GeoPeriX {release}",
    },
    "primary_sidebar_end": ["indices.html"],
    "secondary_sidebar_items": ["page-toc", "edit-this-page", "sourcelink"],
    "show_toc_level": 2,
    "navigation_depth": 3,
    "show_nav_level": 1,
    "footer_start": ["copyright"],
    "footer_end":   ["sphinx-version"],
    "pygments_light_style": "friendly",
    "pygments_dark_style":  "monokai",
}

html_title = f"{project} {release} Documentation"

html_static_path = []

# -- Intersphinx ---------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "h5py": ("https://docs.h5py.org/en/stable", None),
}

# -- Copy-button ---------------------------------------------------------------
# Strip the leading prompt characters so only the command is copied.
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- Autosectionlabel ----------------------------------------------------------
# Prefix every section label with the document name to avoid conflicts.
autosectionlabel_prefix_document = True
