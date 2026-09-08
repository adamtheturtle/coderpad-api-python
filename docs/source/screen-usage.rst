Screen API usage
================

The Screen API is available on the same client via ``screen_api_key``.

.. code-block:: python

   """Screen API usage example."""

   import sys

   from coderpad.client import CoderPad
   from coderpad.screen_types import ScreenInvitation

   client = CoderPad(
       api_key="your-interview-api-key",
       screen_api_key="your-screen-api-key",
   )
   campaigns = client.screen.campaigns.list()
   _ = sys.stdout.write(campaigns[0].name)
   invitation = ScreenInvitation(
       candidate_email="candidate@example.com",
       candidate_name="Ada Lovelace",
   )
   result = client.screen.campaigns.send_invitation(
       campaign_id=campaigns[0].id,
       invitation=invitation,
   )
   if result.test_url is not None:
       _ = sys.stdout.write(result.test_url)
