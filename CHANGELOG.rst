Changelog
=========

.. towncrier release notes start

2026.09.07
----------

- Removed ``client.quota.get()``. Use ``client.organization.get_quota()``,
  which it only delegated to.

- Removed ``PadHistory.replay_to_file`` and ``coderpad.screen.save_screen_report``.
  Callers can write replayed contents or report bytes with ``pathlib.Path``
  directly.

- Add synchronous and asynchronous HTTPX2 transports while retaining HTTPX as
  the default client family.

2026.08.23
----------

- Add ``pads.all()`` to iterate Interview pads across paginated responses.

- Add ``screen.tests.all()`` to iterate Screen tests across paginated responses.

- Expose ``prev_page`` on Interview API ``PaginatedList`` responses.

- Interview API types such as ``Pad``, ``Question``, and ``Language`` are now available from ``coderpad``.

- Exception classes such as ``CoderPadError`` and ``NotFoundError`` are now available from ``coderpad``.

- Documented which ``Question`` and ``Pad`` fields are writable versus read-only in a new "Writable and read-only fields" reference page.

- Validate that ``contents``, ``file_contents``, and ``zip_file`` are mutually exclusive on question create/update.

- Support configurable ``httpx`` timeouts on ``CoderPad`` and ``AsyncCoderPad``.

- Parse JSON API error bodies into optional ``CoderPadError.code`` and ``CoderPadError.message`` attributes.

- Added ``BadGatewayError``, ``ServiceUnavailableError``, and ``GatewayTimeoutError`` for HTTP 502, 503, and 504 responses.

- Defer Screen namespace initialization until first access on CoderPad clients.

- Fail fast with a clear error when Screen methods are called without a ``screen_api_key``.

- Support custom default headers on ``CoderPad`` and ``AsyncCoderPad``.

- Support configuring an ``httpx`` proxy on ``CoderPad`` and ``AsyncCoderPad``.

- Bump PyPI development status classifier from Planning to Beta.

- Fixed the README minimum Python version badge to match ``requires-python`` (3.12).

- Add Screen API usage documentation.

- Document the exception hierarchy in the Sphinx API reference.

- Add ``save_screen_report`` to write Screen report bytes to a file.

- ``SortOrder`` is now a ``StrEnum``, so its values work directly as query strings.

- ``Language`` is now a ``StrEnum``, so its values work directly in API requests.

- Add ``scripts/sync_openapi.py`` to normalize Postman OpenAPI exports
  into the bundled ``openapi.json``.

- Load API keys from ``CODERPAD_API_KEY`` and ``CODERPAD_SCREEN_API_KEY`` via ``from_env()``.

- ``PaginatedList`` and ``ScreenTestsPage`` now include concise ``__repr__`` output for debugging.

- Add ``tests.report_json`` (sync and async) returning a typed
  ``ScreenReport`` from the Screen test session payload.

- Document the public API stability policy.

- Add ``PadHistory.replay_to_file`` to write replayed editor contents to disk.

- Support configuring ``httpx`` connection pool limits on CoderPad clients.

- Document the maintainer workflow for empirically observed API variants
  and link it to towncrier news fragments and the API drift issue template.

- Add ``client.quota.get()`` as an alias for ``client.organization.get_quota()``.

- Validate that Screen invitations include ``candidate_email`` and ``candidate_name`` before send.

2026.08.16
----------

- Add typed synchronous and asynchronous CoderPad Screen clients covering
  campaigns, invitations, tests, reports, pagination, regions, and webhooks.

- Add synchronous and asynchronous organization user listing, with optional
  server-side email filtering.

- Validate client form requests against request-body definitions in the bundled
  OpenAPI specification during tests.

- API resource types are now strict, frozen Pydantic v2 models.  Responses are
  validated with ``model_validate`` and request models support
  ``model_dump``.  Beartype continues to provide runtime type checking
  alongside Pydantic.

2026.07.24
----------

- Expose the optional ``ai_assist_custom_system_prompt`` field on question
  responses so custom AI Assist prompts can be read and synchronized.

2026.07.22.1
------------

- Add ``ai_assist_custom_system_prompt`` to ``questions.update`` so AI Assist
  system prompts can be synchronized for existing questions.

2026.07.22
----------

- Add synchronous and asynchronous support for retrieving and replaying per-file pad editor history.

- Support empirically observed API response variants for binary files, organization metadata, pad interviewer notifications, and question custom databases.

- Add an ``ai_assist_custom_system_prompt`` parameter to ``questions.create``
  to configure AI Assist's system prompt for a question.

2026.06.29
----------

- Add a ``candidate_instructions`` parameter to ``questions.create`` and ``questions.update`` so progressively-revealed candidate instruction blocks can be authored via the API.

2026.05.04
----------


2026.04.01
----------


2026.03.31.2
------------


- Removed support for Python 3.11.
- Changed default ``base_url`` from ``https://api.interview.coderpad.io`` to ``https://app.coderpad.io``.

2026.03.31.1
------------


2026.03.31
----------


2026.03.29.1
------------


2026.03.29
----------
