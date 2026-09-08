Contributing to |project|
=========================

Contributions to this repository must pass tests and linting.

CI is the canonical source of truth.

Install contribution dependencies
---------------------------------

Install Python dependencies in a virtual environment.

.. code-block:: console

   $ pip install --editable . --group dev

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew`_:

.. code-block:: console

   $ brew install enchant

and on Ubuntu with ``apt``:

.. code-block:: console

   $ apt-get install -y enchant

Install ``prek`` hooks:

.. code-block:: console

   $ prek install

Linting
-------

Run lint tools either by committing, or with:

.. code-block:: console

   $ prek run --all-files --hook-stage pre-commit --verbose
   $ prek run --all-files --hook-stage pre-push --verbose
   $ prek run --all-files --hook-stage manual --verbose

.. _Homebrew: https://brew.sh

Running tests
-------------

Run ``pytest``:

.. code-block:: console

   $ pytest

Documentation
-------------

Documentation is built on Read the Docs.

Run the following commands to build and view documentation locally:

.. code-block:: console

   $ uv run --group=dev sphinx-build -M html docs/source docs/build -W
   $ python -c 'import os, webbrowser; webbrowser.open("file://" + os.path.abspath("docs/build/html/index.html"))'

Undocumented API variants
~~~~~~~~~~~~~~~~~~~~~~~~~

CoderPad responses sometimes include fields that are missing from the published OpenAPI specification.
When you extend the client to support a new empirically observed variant, update all of the following:

#. Add a ``newsfragments/<issue>.change.rst`` entry describing the user-visible behavior (see :doc:`release-process`).
#. Extend the bullet list in :doc:`openapi-spec` under empirically observed response fields.
#. Add or extend **synthetic** fixtures and tests so the variant is covered without storing account-specific payloads in the repository.

Continuous integration
----------------------

Tests are run on GitHub Actions.
The configuration for this is in :file:`.github/workflows/`.

Performing a release
--------------------

See :doc:`release-process`.
