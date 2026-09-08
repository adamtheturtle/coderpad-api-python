"""Tests for synchronous CoderPad Screen support."""

# ruff: noqa: PLR2004

import pytest
from pydantic import ValidationError

from coderpad import SCREEN_EU_BASE_URL, CoderPad
from coderpad.exceptions import AuthenticationError
from coderpad.screen_types import (
    ScreenCampaign,
    ScreenInvitation,
    ScreenReport,
    ScreenTest,
)
from tests.conftest import ScreenTransportStub


def _client(
    transport: ScreenTransportStub,
    /,
    *,
    base_url: str,
) -> CoderPad:
    """Create a client using the recording transport."""
    return CoderPad(
        api_key="interview-key",
        screen_api_key="screen-key",
        screen_base_url=base_url,
        screen_transport=transport,
    )


def test_campaigns_and_invitation(
    screen_transport_stub: ScreenTransportStub,
) -> None:
    """Campaigns and invitations use Screen authentication and JSON."""
    transport = screen_transport_stub
    client = _client(transport, base_url=SCREEN_EU_BASE_URL)
    campaigns = client.screen.campaigns.list()
    invitation = ScreenInvitation(
        candidate_email="ada@example.com",
        candidate_name="Ada",
    )
    result = client.screen.campaigns.send_invitation(
        campaign_id=campaigns[0].id,
        invitation=invitation,
    )
    assert campaigns[0].languages == ["python"]
    assert not campaigns[0].pinned
    assert not campaigns[0].archived
    assert result.id == 11
    assert result.test_url == "https://test.example"
    assert transport.calls[0]["headers"] == {"API-Key": "screen-key"}
    assert transport.calls[1]["json"] == {
        "candidate_email": "ada@example.com",
        "candidate_name": "Ada",
    }
    assert f"{transport.calls[0]['url']}".startswith(SCREEN_EU_BASE_URL)
    client.close()


def test_required_integer_fields_are_validated() -> None:
    """Required integer fields reject malformed API values."""
    with pytest.raises(expected_exception=TypeError):
        _ = ScreenCampaign.from_dict(
            data={"id": "not-an-integer", "name": "Bad"}
        )
    assert not bool(ScreenCampaign(id=1, name="Empty").languages)
    assert ScreenTest.from_dict(data={"id": 1}).report is None


def test_malformed_optional_values_use_defaults() -> None:
    """Malformed optional API values do not leak into typed models."""
    assert ScreenReport.from_dict(data={"score": True}).score is None
    test = ScreenTest.from_dict(data={"id": 1, "status": None})
    assert test.status == "unknown"


def test_tests_filters_pagination_and_decoding(
    screen_transport_stub: ScreenTransportStub,
) -> None:
    """Test list filters, pagination, and nested models are preserved."""
    transport = screen_transport_stub
    page = _client(transport, base_url=SCREEN_EU_BASE_URL).screen.tests.list(
        campaign_id=7,
        status="completed",
        tag="python",
        search="Ada",
        product="screen",
        candidate_email="ada@example.com",
        from_time=100,
        to_time=200,
        start=0,
        limit=1,
    )
    assert page.pagination is not None
    assert page.pagination.next_start == 1
    assert page.pagination.has_more_items
    assert page.tests[0].send_time == 1000
    assert page.tests[0].last_activity_time is None
    assert page.tests[0].test_url is None
    assert page.tests[0].questions[0].last_activity_time == 1100
    assert page.tests[0].report is not None
    screen_report = page.tests[0].report
    assert screen_report.duration is None
    assert not bool(screen_report.warnings)
    assert screen_report.points is None
    assert screen_report.score == 90
    assert screen_report.total_duration is None
    assert screen_report.total_points is None
    assert screen_report.comparative_score is None
    assert screen_report.community_stats == [1, 2, 3]
    technology = screen_report.technologies["Python"]
    assert technology.points is None
    assert technology.score == 95
    assert technology.total_points is None
    assert technology.comparative_score is None
    skill = technology.skills["Language"]
    assert skill.points == 9
    assert skill.score == 90
    assert skill.total_points == 10
    assert transport.calls[-1]["params"] == {
        "campaignId": 7,
        "status": "completed",
        "tag": "python",
        "search": "Ada",
        "product": "screen",
        "candidateEmail": "ada@example.com",
        "from": 100,
        "to": 200,
        "start": 0,
        "limit": 1,
    }


def test_get_actions_report_and_webhook(
    screen_transport_stub: ScreenTransportStub,
) -> None:
    """Test retrieval, mutations, PDF bytes, and webhook operations."""
    transport = screen_transport_stub
    screen = _client(transport, base_url=SCREEN_EU_BASE_URL).screen
    test = screen.tests.get(test_id=11, with_community_stats=True)
    screen.tests.cancel(test_id=11)
    screen.tests.resend(test_id=11)
    screen.tests.delete(test_id=11)
    report = screen.tests.report(
        test_id=11,
        report_type="simplified",
        anonymous=True,
    )
    typed_report = screen.tests.report_json(
        test_id=11,
        with_community_stats=True,
    )
    webhook = screen.webhook.get()
    screen.webhook.set(url="https://example.com/new-hook")
    screen.webhook.delete()
    assert test.candidate_name == "Ada"
    assert transport.calls[0]["params"] == {"withCommunityStats": "true"}
    assert report == b"%PDF report"
    assert typed_report.score == 90
    assert webhook.url == "https://example.com/hook"
    assert transport.calls[-2]["json"] == "https://example.com/new-hook"


def test_report_json_raises_when_no_report() -> None:
    """Report_json raises LookupError when the test has no scored
    report.
    """
    transport = ScreenTransportStub(error=False)
    screen = _client(transport, base_url=SCREEN_EU_BASE_URL).screen
    with pytest.raises(
        expected_exception=LookupError,
        match="Screen test 99 has no scored report",
    ):
        _ = screen.tests.report_json(test_id=99)


def test_screen_errors_use_existing_hierarchy() -> None:
    """Screen HTTP failures map to the shared exception hierarchy."""
    with pytest.raises(expected_exception=AuthenticationError):
        _ = _client(
            ScreenTransportStub(error=True), base_url=SCREEN_EU_BASE_URL
        ).screen.campaigns.list()


def test_tests_all_iterates_pages() -> None:
    """Tests.all() yields tests across pagination.next_start pages."""
    transport = ScreenTransportStub(error=False)
    client = _client(transport, base_url=SCREEN_EU_BASE_URL)
    names = [test.candidate_name for test in client.screen.tests.all(limit=1)]
    assert names == ["Ada", "Grace"]
    assert transport.calls[0]["params"] == {"limit": 1}
    assert transport.calls[1]["params"] == {"limit": 1, "start": 1}


def test_invitation_requires_email_and_name() -> None:
    """ScreenInvitation requires candidate email and name."""
    with pytest.raises(
        expected_exception=ValidationError,
        match="candidate_email",
    ):
        _ = ScreenInvitation(candidate_name="Ada")
    with pytest.raises(
        expected_exception=ValidationError,
        match="candidate_name",
    ):
        _ = ScreenInvitation(candidate_email="ada@example.com")


def test_empty_screen_api_key_fails_fast() -> None:
    """Screen requests fail before transport when api_key is empty."""
    transport = ScreenTransportStub(error=False)
    client = CoderPad(
        api_key="interview-key",
        screen_api_key="",
        screen_base_url=SCREEN_EU_BASE_URL,
        screen_transport=transport,
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="Screen API key is required",
    ):
        _ = client.screen.campaigns.list()
    assert not bool(transport.calls)
    client.close()
