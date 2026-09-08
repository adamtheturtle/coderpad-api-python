"""Fixtures for CoderPad API tests."""

import json as json_module
from collections.abc import Callable, Generator
from http import HTTPStatus

import pytest
import respx

from coderpad.async_client import AsyncCoderPad
from coderpad.client import CoderPad
from coderpad.transports import TransportResponse
from tests.openapi_mock import (
    JSONMapping,
    add_openapi_to_respx,
    parse_json_mapping,
)

_BASE_URL = "https://app.coderpad.io"
_LIVE_VARIANT_ORGANIZATION_ID = 42
_AI_ASSIST_CUSTOM_SYSTEM_PROMPT = "Only provide hints."


@pytest.fixture(name="live_variant_organization_id")
def fixture_live_variant_organization_id() -> int:
    """Organization id used by synthetic live-variant fixtures."""
    return _LIVE_VARIANT_ORGANIZATION_ID


@pytest.fixture(name="live_variant_response")
def fixture_live_variant_response() -> Callable[
    ...,
    TransportResponse,
]:
    """Return synthetic examples of empirically observed API variants."""

    def live_variant_response(*, method: str, url: str) -> TransportResponse:
        """Build a synthetic live-variant response for ``url``."""
        if url.endswith("/api/pad_environments/binary"):
            payload: dict[str, object] = {
                "status": "OK",
                "id": 1,
                "pad_id": 2,
                "question_id": None,
                "example_question_id": None,
                "language": "python",
                "file_contents": [
                    {
                        "path": "image.png",
                        "contents": None,
                        "history": "https://example.com/history.json",
                        "binary": True,
                    },
                ],
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            }
        elif url.endswith("/api/organization"):
            payload = {
                "status": "OK",
                "id": _LIVE_VARIANT_ORGANIZATION_ID,
                "organization_name": "Example Organization",
                "user_count": 0,
                "users": [],
                "organization_default_language": "python",
                "single_sign_on_supported": False,
                "teams": [],
                "child_organizations": [],
            }
        elif url.endswith("/api/questions/custom") or (
            method == "POST" and url.endswith("/api/questions/")
        ):
            payload = _question_payload()
        elif method == "GET" and url.endswith("/api/questions/"):
            payload = {
                "status": "OK",
                "questions": [_question_payload()],
                "next_page": None,
                "total": 1,
            }
        else:  # pragma: no cover
            msg = f"Unexpected test URL: {url}"
            raise AssertionError(msg)
        return TransportResponse(
            status_code=HTTPStatus.OK,
            headers={},
            content=json_module.dumps(obj=payload).encode(),
        )

    return live_variant_response


def _question_payload() -> dict[str, object]:
    """Return a question with an empirically observed AI Assist prompt."""
    return {
        "id": 42,
        "title": "FizzBuzz",
        "owner_email": "owner@example.com",
        "language": "python",
        "description": "Write FizzBuzz",
        "candidate_instructions": [],
        "contents": "def fizzbuzz(): ...",
        "shared": False,
        "used": 3,
        "take_home": False,
        "test_cases_enabled": False,
        "solution": None,
        "pad_type": "standard",
        "is_draft": False,
        "author_name": "Author",
        "organization_name": "Org",
        "custom_files": [],
        "created_at": "2026-07-16T00:00:00Z",
        "updated_at": "2026-07-16T00:00:00Z",
        "ai_assist_custom_system_prompt": _AI_ASSIST_CUSTOM_SYSTEM_PROMPT,
    }


@pytest.fixture(name="openapi_spec")
def fixture_openapi_spec(request: pytest.FixtureRequest) -> JSONMapping:
    """Load the OpenAPI spec from the repo."""
    openapi_spec_path = request.config.rootpath / "openapi.json"
    spec_text = openapi_spec_path.read_text(encoding="utf-8")
    return parse_json_mapping(text=spec_text)


@pytest.fixture(name="mock_coderpad_api")
def fixture_mock_coderpad_api(
    openapi_spec: JSONMapping,
) -> Generator[respx.MockRouter]:
    """Provide a respx mock router backed by the OpenAPI spec."""
    with respx.mock(
        base_url=_BASE_URL,
        assert_all_called=False,
    ) as mock_router:
        add_openapi_to_respx(
            mock_obj=mock_router,
            spec=openapi_spec,
            base_url=_BASE_URL,
        )
        yield mock_router


@pytest.fixture(name="coderpad_client")
def fixture_coderpad_client(
    mock_coderpad_api: respx.MockRouter,
) -> CoderPad:
    """Provide a CoderPad client configured against the mock API."""
    # We reference mock_coderpad_api to ensure the mock
    # is active.
    del mock_coderpad_api
    return CoderPad(
        api_key="test-key",
        base_url=_BASE_URL,
    )


@pytest.fixture(name="async_coderpad_client")
def fixture_async_coderpad_client(
    mock_coderpad_api: respx.MockRouter,
) -> AsyncCoderPad:
    """Provide an async CoderPad client against the mock API."""
    del mock_coderpad_api
    return AsyncCoderPad(
        api_key="test-key",
        base_url=_BASE_URL,
    )


_TEST = {
    "id": 11,
    "status": "completed",
    "campaign_id": 7,
    "candidate_name": "Ada",
    "candidate_email": "ada@example.com",
    "tags": ["python"],
    "send_time": 1000,
    "questions": [{"id": 3, "last_activity_time": 1100}],
    "report": {
        "score": 90,
        "technologies": {
            "Python": {
                "score": 95,
                "skills": {
                    "Language": {
                        "points": 9,
                        "score": 90,
                        "total_points": 10,
                    },
                },
            },
        },
        "community_stats": [1, 2, 3],
    },
}


# pylint: disable=too-complex
class ScreenTransportStub:
    """Record requests and return representative Screen responses."""

    def __init__(self, *, error: bool) -> None:
        """Create a recording transport."""
        self.calls: list[dict[str, object]] = []
        self.error = error

    def __call__(  # noqa: C901, PLR0911
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
                [
                    {
                        "id": 7,
                        "name": "Backend",
                        "languages": ["python"],
                    },
                ],
                status=HTTPStatus.OK,
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
                        "tests": [_TEST],
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
            second = {**_TEST, "id": 12, "candidate_name": "Grace"}
            return _response(
                {
                    "tests": [second],
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
                {**_TEST, "id": 99, "report": None},
                status=HTTPStatus.OK,
            )
        if url.endswith("/tests/11"):
            return _response(_TEST, status=HTTPStatus.OK)
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


@pytest.fixture(name="screen_transport_stub")
def fixture_screen_transport_stub() -> ScreenTransportStub:
    """Provide a Screen transport stub that records requests."""
    return ScreenTransportStub(error=False)
