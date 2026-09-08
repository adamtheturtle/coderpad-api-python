Writable and read-only fields
=============================

The :class:`~coderpad.types.Question` and :class:`~coderpad.types.Pad` models expose more fields than the ``create`` and ``update`` methods accept.
A field that is present when you read a resource is not necessarily a field that you can write.

This page documents which fields are writable so that the gap is explicit.
It is especially relevant when syncing resources from source control, where a read field that cannot be written is surprising.

Questions
---------

Writable fields are accepted by
:meth:`coderpad.client.QuestionsNamespace.create` and
:meth:`coderpad.client.QuestionsNamespace.update`.  Every other field
on :class:`~coderpad.types.Question` is populated by the server and returned on read only.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Field
     - Write support
     - Notes
   * - ``title``
     - Create and update
     - Required on create.
   * - ``language``
     - Create and update
     - Required on create.
   * - ``description``
     - Create and update
     -
   * - ``contents``
     - Create and update
     - Cannot be combined with ``file_contents``.
   * - ``solution``
     - Create and update
     -
   * - ``file_contents``
     - Create and update
     - For multi-file questions.  Maps to the read-side pad
       environment files rather than to a single field.
   * - ``zip_file``
     - Create and update
     - Upload alternative to ``file_contents``.
   * - ``candidate_instructions``
     - Read only
     - Write support tracked in issue #196.
   * - ``test_cases``
     - Read only
     -
   * - ``test_cases_enabled``
     - Read only
     -
   * - ``contents_for_test_cases``
     - Read only
     -
   * - ``take_home``
     - Read only
     -
   * - ``shared``
     - Read only
     -
   * - ``is_draft``
     - Read only
     -
   * - ``custom_files``
     - Read only
     -
   * - ``id``
     - Read only
     - Server-assigned.
   * - ``owner_email``
     - Read only
     - Server-assigned.
   * - ``used``
     - Read only
     - Server-managed usage count.
   * - ``pad_type``
     - Read only
     - Server-managed.
   * - ``author_name``
     - Read only
     - Server-managed.
   * - ``organization_name``
     - Read only
     - Server-managed.
   * - ``public_take_home_setting_id``
     - Read only
     - Server-managed.
   * - ``created_at``
     - Read only
     - Server-managed timestamp.
   * - ``updated_at``
     - Read only
     - Server-managed timestamp.

Pads
----

Writable fields are accepted by
:meth:`coderpad.client.PadsNamespace.create` and
:meth:`coderpad.client.PadsNamespace.update`.  Every other field on
:class:`~coderpad.types.Pad` is populated by the server and returned
on read only.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Field
     - Write support
     - Notes
   * - ``title``
     - Create and update
     -
   * - ``language``
     - Create and update
     -
   * - ``contents``
     - Create and update
     -
   * - ``notes``
     - Create and update
     - Private notes for the interviewer.
   * - ``question_id``
     - Create only
     - Seeds the pad from an existing question.  Not a field on
       the read model; see ``question_ids`` instead.
   * - ``ended``
     - Update only
     - Set to ``True`` to end the interview.  Reflected on read as
       ``ended_at``.
   * - ``deleted``
     - Update only
     - Set to ``True`` to delete the pad.
   * - ``id``
     - Read only
     - Server-assigned.
   * - ``state``
     - Read only
     - Server-managed.
   * - ``owner_email``
     - Read only
     - Server-assigned.
   * - ``private``
     - Read only
     - Server-managed.
   * - ``execution_enabled``
     - Read only
     - Server-managed.
   * - ``participants``
     - Read only
     - Server-managed.
   * - ``events``
     - Read only
     - Server-managed.
   * - ``ended_at``
     - Read only
     - Set by passing ``ended`` to ``update``.
   * - ``url``
     - Read only
     - Server-assigned.
   * - ``playback``
     - Read only
     - Server-assigned.
   * - ``drawing``
     - Read only
     - Server-managed.
   * - ``type``
     - Read only
     - Server-managed.
   * - ``question_ids``
     - Read only
     - Seed questions via ``question_id`` on ``create``.
   * - ``pad_environment_ids``
     - Read only
     - Server-managed.
   * - ``active_environment_id``
     - Read only
     - Server-managed.
   * - ``team``
     - Read only
     - Server-managed.
   * - ``history``
     - Read only
     - Server-managed.
   * - ``created_at``
     - Read only
     - Server-managed timestamp.
   * - ``updated_at``
     - Read only
     - Server-managed timestamp.
