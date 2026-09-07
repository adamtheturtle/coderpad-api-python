"""Configuration for Sphinx."""

import importlib.metadata
from pathlib import Path

from packaging.specifiers import SpecifierSet
from sphinx_pyproject import SphinxConfig

_pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
_pyproject_config = SphinxConfig(
    pyproject_file=_pyproject_file,
    config_overrides={"version": None},
)

project = _pyproject_config.name
author = _pyproject_config.author

extensions = [
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_substitution_extensions",
    "sphinxcontrib.spelling",
    "sphinxcontrib.towncrier.ext",
]

# Render the unreleased ``newsfragments/`` entries into
# ``docs/source/unreleased.rst`` so the Sphinx spelling, doc-build and
# link-checking gates cover the prose before it is assembled into
# CHANGELOG.rst at release time.
towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = f"{_pyproject_file.parent}"

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project_copyright = f"%Y, {author}"

# Exclude the prompt from copied code with sphinx_copybutton.
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html#automatic-exclusion-of-prompts-from-the-copies.
copybutton_exclude = ".linenos, .gp"

project_metadata = importlib.metadata.metadata(distribution_name=project)
requires_python = project_metadata["Requires-Python"]
specifiers = SpecifierSet(specifiers=requires_python)
(specifier,) = specifiers
if specifier.operator != ">=":
    msg = (
        f"We only support '>=' for Requires-Python, got {specifier.operator}."
    )
    raise ValueError(msg)
minimum_python_version = specifier.version

language = "en"

# The name of the syntax highlighting style to use.
pygments_style = "sphinx"

html_theme = "furo"
html_title = project
html_show_copyright = False
html_show_sphinx = False
html_show_sourcelink = False
html_theme_options = {
    "sidebar_hide_name": False,
    "source_repository": "https://github.com/adamtheturtle/coderpad/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}

# Output file base name for HTML help builder.
htmlhelp_basename = "CODERPADPYdoc"
intersphinx_mapping = {
    "python": (f"https://docs.python.org/{minimum_python_version}", None),
}
nitpicky = True
nitpick_ignore: list[tuple[str, str]] = [
    ("py:class", "coderpad.types._T"),
    # The HTTP client inventories do not expose these configuration classes;
    # keep the typed annotations without making the docs build fail.
    ("py:class", "httpx.Limits"),
    ("py:class", "httpx.Proxy"),
    ("py:class", "httpx.Timeout"),
    ("py:class", "httpx2.Limits"),
    ("py:class", "httpx2.Proxy"),
    ("py:class", "httpx2.Timeout"),
]
nitpick_ignore_regex = [
    (r"py:class", r"coderpad\._dict_types\..*"),
]
warning_is_error = True

autoclass_content = "both"

# Retry link checking to avoid transient network errors.
linkcheck_retries = 5

spelling_word_list_filename = "../../spelling_private_dict.txt"

autodoc_member_order = "bysource"

rst_prolog = f"""
.. |project| replace:: {project}
.. |minimum-python-version| replace:: {minimum_python_version}
.. |github-owner| replace:: adamtheturtle
.. |github-repository| replace:: coderpad
"""
