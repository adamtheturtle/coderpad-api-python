Public API stability
====================

``coderpad-py`` follows a Semantic Versioning inspired policy for its public Python API.

What is public
--------------

The public API is whatever is documented in the Sphinx API reference and exported from the ``coderpad`` package (including ``coderpad.client``, ``coderpad.async_client``, ``coderpad.screen``, ``coderpad.async_screen``, ``coderpad.types``, ``coderpad.screen_types``, ``coderpad.exceptions``, and ``coderpad.transports``).

Compatibility expectations
--------------------------

* **Patch** releases may include bug fixes and documentation updates.
  They should not change documented behavior in incompatible ways.
* **Minor** releases may add APIs, optional parameters, and new documented fields on models.
  Existing calls should keep working.
* **Major** releases may remove or rename public APIs, or change required parameters and return types.

Private modules and names prefixed with an underscore are not part of the public API and may change without notice.

The published OpenAPI document and upstream CoderPad HTTP APIs can evolve independently.
The client aims to absorb non-breaking server additions (such as new JSON fields) without requiring a major version bump.
