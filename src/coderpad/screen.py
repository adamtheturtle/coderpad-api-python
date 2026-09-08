"""Synchronous CoderPad Screen API namespaces."""

import builtins
from collections.abc import Iterator
from http import HTTPStatus

from beartype import beartype

from coderpad.exceptions import CoderPadError
from coderpad.screen_types import (
    ScreenCampaign,
    ScreenInvitation,
    ScreenInvitationResult,
    ScreenReport,
    ScreenTest,
    ScreenTestsPage,
    ScreenWebhook,
)
from coderpad.transports import JSONTransport, TransportResponse

SCREEN_US_BASE_URL = "https://www.codingame.com"
SCREEN_EU_BASE_URL = "https://www.codingame.eu"
_SCREEN_PREFIX = "/assessment/api/v1.1"


@beartype
class _ScreenNamespace:
    """Shared synchronous Screen request handling."""

    def __init__(
        self,
        *,
        transport: JSONTransport,
        api_key: str,
        base_url: str,
        default_headers: dict[str, str] | None,
    ) -> None:
        """Create shared Screen request state."""
        self.transport: JSONTransport = transport
        self.base_url: str = base_url.rstrip("/")
        self.api_key: str = api_key
        self.headers: dict[str, str] = {
            **(default_headers if default_headers is not None else {}),
            "API-Key": api_key,
        }

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, str | int] | None,
        json: object | None,
    ) -> TransportResponse:
        """Make a Screen request and map HTTP failures."""
        if not bool(self.api_key):
            msg = (
                "Screen API key is required; pass screen_api_key when "
                "creating the client."
            )
            raise ValueError(msg)
        response = self.transport(
            method=method,
            url=self.base_url + _SCREEN_PREFIX + path,
            headers=self.headers,
            params=params,
            data=None,
            files=None,
            json=json,
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise CoderPadError.from_response(response=response)
        return response


@beartype
class ScreenCampaignsNamespace(_ScreenNamespace):
    """Screen campaign operations."""

    def list(self) -> builtins.list[ScreenCampaign]:
        """List assessment campaigns."""
        response = self._request(
            method="GET", path="/campaigns", params=None, json=None
        )
        raw_campaigns: object = response.json()
        return ScreenCampaign.list_from_value(value=raw_campaigns)

    def send_invitation(
        self,
        *,
        campaign_id: int,
        invitation: ScreenInvitation,
    ) -> ScreenInvitationResult:
        """Create a test session and optionally email the candidate."""
        response = self._request(
            method="POST",
            path=f"/campaigns/{campaign_id}/actions/send",
            json=invitation.model_dump(exclude_none=True),
            params=None,
        )
        return ScreenInvitationResult.from_dict(data=response.json())


@beartype
class ScreenTestsNamespace(_ScreenNamespace):
    """Screen test-session operations."""

    def list(
        self,
        *,
        campaign_id: int | None = None,
        status: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        product: str | None = None,
        candidate_email: str | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        start: int | None = None,
        limit: int | None = None,
    ) -> ScreenTestsPage:
        """List one offset-paginated page of tests.

        Pass ``page.pagination.next_start`` to ``start`` while
        ``has_more_items`` is true to traverse subsequent pages.
        """
        params: dict[str, str | int] = {}
        values: tuple[tuple[str, str | int | None], ...] = (
            ("campaignId", campaign_id),
            ("status", status),
            ("tag", tag),
            ("search", search),
            ("product", product),
            ("candidateEmail", candidate_email),
            ("from", from_time),
            ("to", to_time),
            ("start", start),
            ("limit", limit),
        )
        params.update(
            (key, value) for key, value in values if value is not None
        )
        response = self._request(
            method="GET", path="/tests", params=params, json=None
        )
        return ScreenTestsPage.from_dict(data=response.json())

    def all(
        self,
        *,
        campaign_id: int | None = None,
        status: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        product: str | None = None,
        candidate_email: str | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        limit: int | None = None,
    ) -> Iterator[ScreenTest]:
        """Yield all tests across offset-paginated responses.

        Args:
            campaign_id: Filter by campaign id.
            status: Filter by status.
            tag: Filter by tag.
            search: Free-text search.
            product: Filter by product.
            candidate_email: Filter by candidate email.
            from_time: Lower bound timestamp.
            to_time: Upper bound timestamp.
            limit: Page size.

        Yields:
            Each test until ``pagination.has_more_items`` is false.
        """
        start: int | None = None
        while True:
            page = self.list(
                campaign_id=campaign_id,
                status=status,
                tag=tag,
                search=search,
                product=product,
                candidate_email=candidate_email,
                from_time=from_time,
                to_time=to_time,
                start=start,
                limit=limit,
            )
            yield from page.tests
            pagination = page.pagination
            if (
                pagination is None
                or not pagination.has_more_items
                or pagination.next_start is None
            ):
                break
            start = pagination.next_start

    def get(
        self,
        *,
        test_id: int,
        with_community_stats: bool = False,
    ) -> ScreenTest:
        """Retrieve one test session."""
        params: dict[str, str | int] = (
            {"withCommunityStats": "true"} if with_community_stats else {}
        )
        response = self._request(
            method="GET",
            path=f"/tests/{test_id}",
            params=params,
            json=None,
        )
        return ScreenTest.from_dict(data=response.json())

    def cancel(self, *, test_id: int) -> None:
        """Cancel a test invitation."""
        _ = self._request(
            method="POST",
            path=f"/tests/{test_id}/actions/cancel",
            params=None,
            json=None,
        )

    def resend(self, *, test_id: int) -> None:
        """Resend a test invitation."""
        _ = self._request(
            method="POST",
            path=f"/tests/{test_id}/actions/resend",
            params=None,
            json=None,
        )

    def delete(self, *, test_id: int) -> None:
        """Delete a test session."""
        _ = self._request(
            method="DELETE", path=f"/tests/{test_id}", params=None, json=None
        )

    def report(
        self,
        *,
        test_id: int,
        report_type: str | None = None,
        anonymous: bool | None = None,
        include_rank: bool | None = None,
        include_comparative_score: bool | None = None,
    ) -> bytes:
        """Download a test report without writing it to disk."""
        params: dict[str, str | int] = {}
        values: tuple[tuple[str, str | bool | None], ...] = (
            ("report_type", report_type),
            ("anonymous", anonymous),
            ("include_rank", include_rank),
            ("include_comparative_score", include_comparative_score),
        )
        for key, value in values:
            if isinstance(value, bool):
                params[key] = "true" if value else "false"
            elif value is not None:
                params[key] = value
        return self._request(
            method="GET",
            path=f"/tests/{test_id}/report",
            params=params,
            json=None,
        ).content

    def report_json(
        self,
        *,
        test_id: int,
        with_community_stats: bool = False,
    ) -> ScreenReport:
        """Return the typed JSON report embedded in a test session.

        The Screen ``/tests/{id}/report`` endpoint serves PDF bytes.
        Scored report fields are returned on ``GET /tests/{id}`` as
        ``ScreenTest.report``; this helper fetches that payload and
        returns the typed report.

        Args:
            test_id: The Screen test session id.
            with_community_stats: Whether to include community
                statistics on the report.

        Returns:
            The typed scored report.

        Raises:
            LookupError: If the test exists but has no report yet.
        """
        test = self.get(
            test_id=test_id,
            with_community_stats=with_community_stats,
        )
        if test.report is None:
            message = f"Screen test {test_id} has no scored report"
            raise LookupError(message)
        return test.report


@beartype
class ScreenWebhookNamespace(_ScreenNamespace):
    """Screen webhook operations."""

    def get(self) -> ScreenWebhook:
        """Retrieve webhook configuration."""
        response = self._request(
            method="GET", path="/webhook", params=None, json=None
        )
        return ScreenWebhook.from_dict(data=response.json())

    def set(self, *, url: str) -> None:
        """Set or replace the webhook URL."""
        _ = self._request(
            method="POST", path="/webhook", json=url, params=None
        )

    def delete(self) -> None:
        """Delete the webhook configuration."""
        _ = self._request(
            method="DELETE", path="/webhook", params=None, json=None
        )


@beartype
class ScreenNamespace(_ScreenNamespace):
    """Root namespace for the synchronous Screen API."""

    def __init__(
        self,
        *,
        transport: JSONTransport,
        api_key: str,
        base_url: str,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        """Create the root Screen namespace."""
        super().__init__(
            transport=transport,
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )
        self.campaigns: ScreenCampaignsNamespace = ScreenCampaignsNamespace(
            transport=transport,
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )
        self.tests: ScreenTestsNamespace = ScreenTestsNamespace(
            transport=transport,
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )
        self.webhook: ScreenWebhookNamespace = ScreenWebhookNamespace(
            transport=transport,
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )
