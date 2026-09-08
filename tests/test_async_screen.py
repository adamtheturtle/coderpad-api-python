"""Tests for asynchronous CoderPad Screen support."""

# ruff: noqa: C901, PLR0911, PLR2004
# pylint: disable=too-complex

import json as json_module
from http import HTTPStatus

import pytest

from coderpad import SCREEN_EU_BASE_URL, AsyncCoderPad
from coderpad.exceptions import AuthenticationError
from coderpad.screen_types import ScreenInvitation
from coderpad.transports import TransportResponse


class _AsyncScreenTransport:
    """Record asynchronous Screen requests."""

    def __init__(self, *, error: bool) -> None:
        """Create a recording transport."""
        self.calls: list[dict[str, object]] = []
        self.error = error

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: dict[str, tuple[str, bytes, str]] | None,
        json: object | None,
    ) -> TransportResponse:
        """Return a response selected by the request path."""
        del data, files
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params if params is not None else {},
                "json": json,
            },
        )
        if self.error:
            return _response(
                {"code": "Unauthorized", "message": "Invalid API key"},
                status=HTTPStatus.UNAUTHORIZED,
            )
        if url.endswith("/campaigns"):
            return _response(
                [{"id": 7, "name": "Backend"}], status=HTTPStatus.OK
            )
        if url.endswith("/campaigns/7/actions/send"):
            return _response(
                {"id": 11, "test_url": "https://test.example"},
                status=HTTPStatus.OK,
            )
        if url.endswith("/tests"):
            start = 0
            if params is not None and "start" in params:
                start = int(params["start"])
            if start == 0:
                return _response(
                    {
                        "tests": [
                            {
                                "id": 11,
                                "status": "completed",
                                "candidate_name": "Ada",
                                "report": dict[str, object](),
                            },
                        ],
                        "pagination": {
                            "start": 0,
                            "limit": 1,
                            "total": 2,
                            "has_more_items": True,
                            "next_start": 1,
                        },
                    },
                    status=HTTPStatus.OK,
                )
            return _response(
                {
                    "tests": [
                        {
                            "id": 12,
                            "status": "completed",
                            "candidate_name": "Grace",
                            "report": dict[str, object](),
                        },
                    ],
                    "pagination": {
                        "start": 1,
                        "limit": 1,
                        "total": 2,
                        "has_more_items": False,
                        "next_start": None,
                    },
                },
                status=HTTPStatus.OK,
            )
        if url.endswith("/tests/11/report"):
            return TransportResponse(
                status_code=HTTPStatus.OK,
                headers={"content-type": "application/pdf"},
                content=b"%PDF report",
            )
        if url.endswith("/tests/99"):
            return _response(
                {"id": 99, "status": "completed", "report": None},
                status=HTTPStatus.OK,
            )
        if url.endswith("/tests/11"):
            return _response(
                {
                    "id": 11,
                    "status": "completed",
                    "report": dict[str, object](),
                },
                status=HTTPStatus.OK,
            )
        if url.endswith("/webhook") and method == "GET":
            return _response(
                {"url": "https://example.com/hook"}, status=HTTPStatus.OK
            )
        return TransportResponse(
            status_code=HTTPStatus.NO_CONTENT,
            headers={},
            content=b"",
        )


def _response(
    value: object,
    /,
    *,
    status: HTTPStatus,
) -> TransportResponse:
    """Create a JSON transport response."""
    return TransportResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        content=json_module.dumps(obj=value).encode(),
    )


def _client(transport: _AsyncScreenTransport, /) -> AsyncCoderPad:
    """Create an asynchronous client using the recording transport."""
    return AsyncCoderPad(
        api_key="interview-key",
        screen_api_key="screen-key",
        screen_transport=transport,
    )


@pytest.mark.asyncio
async def test_async_screen_matches_sync_surface() -> None:
    """The asynchronous namespaces expose equivalent operations."""
    recorder = _AsyncScreenTransport(error=False)
    client = _client(recorder)
    screen = client.screen
    campaigns = await screen.campaigns.list()
    invitation = await screen.campaigns.send_invitation(
        campaign_id=7,
        invitation=ScreenInvitation(
            candidate_email="ada@example.com",
            candidate_name="Ada",
        ),
    )
    page = await screen.tests.list(start=0, limit=1)
    test = await screen.tests.get(test_id=11, with_community_stats=True)
    await screen.tests.cancel(test_id=11)
    await screen.tests.resend(test_id=11)
    await screen.tests.delete(test_id=11)
    report = await screen.tests.report(
        test_id=11,
        report_type="full",
        anonymous=True,
        include_rank=False,
    )
    typed_report = await screen.tests.report_json(
        test_id=11,
        with_community_stats=True,
    )
    webhook = await screen.webhook.get()
    await screen.webhook.set(url="https://example.com/hook")
    await screen.webhook.delete()
    assert campaigns[0].id == 7
    assert invitation.id == 11
    assert page.pagination is not None
    assert page.pagination.total == 2
    assert test.report is not None
    assert report == b"%PDF report"
    assert typed_report.score == test.report.score
    assert recorder.calls[7]["params"] == {
        "report_type": "full",
        "anonymous": "true",
        "include_rank": "false",
    }
    assert webhook.url == "https://example.com/hook"
    await client.aclose()


@pytest.mark.asyncio
async def test_async_screen_errors_use_existing_hierarchy() -> None:
    """Async Screen failures map to the shared exception hierarchy."""
    recorder = _AsyncScreenTransport(error=True)
    screen = _client(recorder).screen
    with pytest.raises(expected_exception=AuthenticationError):
        await screen.campaigns.list()


@pytest.mark.asyncio
async def test_async_report_json_raises_when_no_report() -> None:
    """Async report_json raises LookupError when the test has no
    report.
    """
    recorder = _AsyncScreenTransport(error=False)
    screen = _client(recorder).screen
    with pytest.raises(
        expected_exception=LookupError,
        match="Screen test 99 has no scored report",
    ):
        await screen.tests.report_json(test_id=99)


@pytest.mark.asyncio
async def test_async_tests_all_iterates_pages() -> None:
    """Async tests.all() yields tests across pagination pages."""
    recorder = _AsyncScreenTransport(error=False)
    client = _client(recorder)
    names = [
        test.candidate_name async for test in client.screen.tests.all(limit=1)
    ]
    assert names == ["Ada", "Grace"]
    await client.aclose()


@pytest.mark.asyncio
async def test_async_empty_screen_api_key_fails_fast() -> None:
    """Async Screen requests fail before transport when api_key is
    empty.
    """
    recorder = _AsyncScreenTransport(error=False)
    client = AsyncCoderPad(
        api_key="interview-key",
        screen_api_key="",
        screen_base_url=SCREEN_EU_BASE_URL,
        screen_transport=recorder,
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="Screen API key is required",
    ):
        await client.screen.campaigns.list()
    assert not bool(recorder.calls)
    await client.aclose()
