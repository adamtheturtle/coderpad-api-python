|Build Status| |PyPI|

coderpad-py
===========

Python library for the CoderPad Interview API.

Installation
------------

.. code-block:: shell

   pip install coderpad-py

This is tested on Python |minimum-python-version|\+.

Getting Started
---------------

.. code-block:: python

   """Example usage."""

   import sys

   from coderpad.client import CoderPad

   client = CoderPad(api_key="your-api-key")
   pad = client.pads.create(title="Interview", language="python")
   sys.stdout.write(pad.title)
   for listed_pad in client.pads.list():
       sys.stdout.write(listed_pad.title)
   org = client.organization.get()
   sys.stdout.write(org.organization_name)
   for user in client.organization.users.list():
       sys.stdout.write(user.email)

The organization users endpoint also supports server-side email filtering:

.. code-block:: python

   """Filter organization users by email."""

   from coderpad.client import CoderPad

   client = CoderPad(api_key="your-api-key")
   users = client.organization.users.list(email="person@example.com")

The equivalent asynchronous operation is
``await client.organization.users.list(email="person@example.com")``.

HTTPX2 transports
-----------------

HTTPX remains the default client family. To opt in to HTTPX2, construct the
HTTPX2 transport explicitly and pass it to the client. The standard
``coderpad-py`` installation includes both client families.

.. code-block:: python

   """Configure CoderPad to use HTTPX2."""

   import sys

   import httpx2

   from coderpad.client import CoderPad
   from coderpad.transports import HTTPX2Transport

   transport = HTTPX2Transport(timeout=httpx2.Timeout(timeout=10))
   with CoderPad(api_key="your-api-key", transport=transport) as client:
       sys.stdout.write(client.base_url)

Use ``AsyncHTTPX2Transport`` with ``AsyncCoderPad`` for asynchronous calls.
The ``limits``, ``proxy`` and ``timeout`` arguments passed to these transports
accept HTTPX2 configuration objects. Do not pass equivalent ``httpx`` objects
across the package boundary. If the Screen API should also use HTTPX2, pass a
separate HTTPX2 transport as ``screen_transport``.

Existing HTTPX users do not need to change anything. Migrating to HTTPX2 only
requires selecting the new transport; the CoderPad client methods and returned
models are unchanged.

CoderPad Screen
---------------

Screen uses a separate API key and host from Interview:

.. code-block:: python

   """List Screen campaigns and candidate tests."""

   from coderpad import CoderPad

   client = CoderPad(
       api_key="your-interview-api-key",
       screen_api_key="your-screen-api-key",
   )
   campaigns = client.screen.campaigns.list()
   page = client.screen.tests.list(campaign_id=campaigns[0].id, limit=50)
   assert page.pagination is not None

Screen test listings use offset pagination. While
``page.pagination.has_more_items`` is true, request the next page with
``start=page.pagination.next_start``. Use ``SCREEN_EU_BASE_URL`` as
``screen_base_url`` for EU-hosted organizations. All Screen operations have
equivalent methods on ``AsyncCoderPad``.


Environment variables
---------------------

Set ``CODERPAD_API_KEY`` for the Interview API. Optionally set
``CODERPAD_SCREEN_API_KEY`` for Screen. Then construct a client with
``CoderPad.from_env()`` or ``AsyncCoderPad.from_env()``:

.. code-block:: python

   """Load API keys from the environment."""

   import sys

   from coderpad.client import CoderPad

   client = CoderPad.from_env()
   sys.stdout.write(client.base_url)

Full Documentation
------------------

See the `full documentation <https://adamtheturtle.github.io/coderpad-api-python/>`__.

.. |Build Status| image:: https://github.com/adamtheturtle/coderpad-api-python/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/coderpad-api-python/actions
.. |PyPI| image:: https://badge.fury.io/py/coderpad-py.svg
   :target: https://badge.fury.io/py/coderpad-py
.. |minimum-python-version| replace:: 3.12
