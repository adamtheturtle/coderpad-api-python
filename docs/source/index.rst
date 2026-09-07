|project|
=========

Installation
------------

.. code-block:: console

   $ pip install coderpad-py

This is tested on Python |minimum-python-version|\+.

Usage
-----

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

See the :doc:`api-reference` for full usage details, including the exception hierarchy.

Reference
---------

.. toctree::
   :maxdepth: 3

   api-reference
   field-reference
   stability
   screen-usage
   openapi-spec
   contributing
   release-process
   unreleased
   changelog
