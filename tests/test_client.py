"""Tests for the CoderPad client."""

import json
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import httpx2
import pytest
import respx

from coderpad.client import CoderPad
from coderpad.exceptions import (
    AuthenticationError,
    BadGatewayError,
    BadRequestError,
    CoderPadError,
    ForbiddenError,
    GatewayTimeoutError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
)
from coderpad.transports import (
    HTTPStatusError,
    HTTPX2Transport,
    HTTPXTransport,
    Transport,
    TransportResponse,
)
from coderpad.types import (
    CandidateInstruction,
    Language,
    OrganizationUser,
    QuestionFileContent,
    SortOrder,
)


class TestCoderPad:
    """Tests for ``CoderPad``."""

    @staticmethod
    def test_default_base_url() -> None:
        """The default base URL is the CoderPad app."""
        client = CoderPad(api_key="test-key")
        assert client.base_url == "https://app.coderpad.io"

    @staticmethod
    def test_custom_base_url() -> None:
        """A custom base URL can be provided."""
        client = CoderPad(
            api_key="test-key",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    @staticmethod
    def test_custom_transport(
        mock_coderpad_api: object,
    ) -> None:
        """A custom transport can be provided."""
        del mock_coderpad_api
        transport = HTTPXTransport()
        client = CoderPad(
            api_key="test-key",
            transport=transport,
        )
        result = client.pads.list()
        assert result.total >= 0

    @staticmethod
    def test_mock_api_available(
        coderpad_client: CoderPad,
    ) -> None:
        """The mock API fixture provides a working mock router."""
        result = coderpad_client.pads.list()
        assert result.total >= 0

    @staticmethod
    def test_close() -> None:
        """The client can be closed."""
        client = CoderPad(api_key="test-key")
        client.close()

    @staticmethod
    def test_context_manager() -> None:
        """The client can be used as a context manager."""
        with CoderPad(api_key="test-key") as client:
            assert isinstance(client, CoderPad)

    @staticmethod
    def test_close_transport_without_close() -> None:
        """Closing works when the transport has no close method."""

        class _NoCloseTransport:
            """A transport without a close method."""

            def __call__(
                self,
                *,
                method: str,
                url: str,
                headers: dict[str, str],
                params: dict[str, str | int] | None,
                data: dict[str, str] | None,
                files: (dict[str, tuple[str, bytes, str]] | None),
            ) -> TransportResponse:  # pragma: no cover
                """Make a request."""
                raise NotImplementedError

        client = CoderPad(
            api_key="test-key",
            transport=_NoCloseTransport(),
        )
        client.close()

    @staticmethod
    def test_default_headers_merged_preserving_authorization() -> None:
        """Default headers merge while Authorization stays the API
        token.
        """
        client = CoderPad(
            api_key="secret",
            default_headers={
                "User-Agent": "coderpad-tests",
                "Authorization": "should-not-win",
            },
        )
        assert client.pads.headers == {
            "User-Agent": "coderpad-tests",
            "Authorization": 'Token token="secret"',
        }
        client.close()

    @staticmethod
    def test_default_headers_merged_preserving_screen_api_key() -> None:
        """Default headers merge while Screen API-Key stays the Screen key."""
        client = CoderPad(
            api_key="interview",
            screen_api_key="screen-secret",
            default_headers={
                "User-Agent": "coderpad-tests",
                "API-Key": "should-not-win",
            },
        )
        assert client.screen.headers == {
            "User-Agent": "coderpad-tests",
            "API-Key": "screen-secret",
        }
        client.close()

    @staticmethod
    def test_limits_forwarded_to_default_transport() -> None:
        """CoderPad forwards limits to the default HTTPX transport."""
        limits = httpx.Limits(max_connections=10)
        client = CoderPad(api_key="test-key", limits=limits)
        transport = client.pads.transport
        assert isinstance(transport, HTTPXTransport)
        assert transport.limits is limits
        client.close()

    @staticmethod
    def test_timeout_forwarded_to_default_transport() -> None:
        """CoderPad forwards timeout to the default HTTPX transport."""
        timeout = httpx.Timeout(timeout=7.5)
        client = CoderPad(api_key="test-key", timeout=timeout)
        transport = client.pads.transport
        assert isinstance(transport, HTTPXTransport)
        assert transport.timeout == timeout
        client.close()

    @staticmethod
    def test_proxy_forwarded_to_default_transport() -> None:
        """CoderPad forwards proxy to the default HTTPX transport."""
        proxy = "http://proxy.example:8080"
        client = CoderPad(api_key="test-key", proxy=proxy)
        transport = client.pads.transport
        assert isinstance(transport, HTTPXTransport)
        assert transport.proxy == proxy
        client.close()

    @staticmethod
    def test_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
        """From_env loads Interview and Screen keys from the
        environment.
        """
        monkeypatch.setenv(name="CODERPAD_API_KEY", value="env-interview")
        monkeypatch.setenv(name="CODERPAD_SCREEN_API_KEY", value="env-screen")
        client = CoderPad.from_env()
        assert client.pads.headers["Authorization"] == (
            'Token token="env-interview"'
        )
        assert client.screen.headers["API-Key"] == "env-screen"
        client.close()

    @staticmethod
    def test_from_env_requires_api_key(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """From_env raises when CODERPAD_API_KEY is missing."""
        monkeypatch.delenv(name="CODERPAD_API_KEY", raising=False)
        monkeypatch.delenv(name="CODERPAD_SCREEN_API_KEY", raising=False)
        with pytest.raises(expected_exception=KeyError):
            CoderPad.from_env()

    @staticmethod
    def test_screen_lazy_requires_api_key() -> None:
        """Accessing screen without a Screen API key raises ValueError."""
        client = CoderPad(api_key="test-key")
        with pytest.raises(
            expected_exception=ValueError,
            match="screen_api_key",
        ):
            _ = client.screen
        client.close()

    @staticmethod
    def test_screen_lazy_initialized_once() -> None:
        """Screen namespace is created on first access and reused."""
        client = CoderPad(
            api_key="test-key",
            screen_api_key="screen-key",
        )
        first = client.screen
        second = client.screen
        assert first is second
        client.close()

    @staticmethod
    def test_screen_with_provided_transport() -> None:
        """Providing screen_transport closes that transport with the
        client.
        """
        transport = HTTPXTransport()
        client = CoderPad(
            api_key="test-key",
            screen_api_key="screen-key",
            screen_transport=transport,
        )
        assert client.screen.headers["API-Key"] == "screen-key"
        client.close()


class TestHTTPXTransport:
    """Tests for ``HTTPXTransport``."""

    @staticmethod
    def test_is_transport() -> None:
        """HTTPXTransport satisfies the Transport protocol."""
        assert isinstance(HTTPXTransport(), Transport)

    @staticmethod
    def test_close() -> None:
        """The transport can be closed."""
        transport = HTTPXTransport()
        transport.close()

    @staticmethod
    def test_context_manager() -> None:
        """The transport can be used as a context manager."""
        with HTTPXTransport() as transport:
            assert isinstance(transport, HTTPXTransport)

    @staticmethod
    def test_limits_passed_to_httpx_client() -> None:
        """Connection pool limits are stored on the HTTPX transport."""
        limits = httpx.Limits(max_connections=5)
        transport = HTTPXTransport(limits=limits)
        assert transport.limits is limits
        transport.close()

    @staticmethod
    def test_timeout_passed_to_httpx_client() -> None:
        """A timeout is forwarded to the underlying httpx client."""
        timeout = httpx.Timeout(timeout=12.5)
        transport = HTTPXTransport(timeout=timeout)
        assert transport.timeout == timeout
        transport.close()

    @staticmethod
    def test_float_timeout_passed_to_httpx_client() -> None:
        """A float timeout is accepted by the HTTPX transport."""
        float_timeout = 3.0
        transport = HTTPXTransport(timeout=float_timeout)
        assert transport.timeout == float_timeout
        transport.close()

    @staticmethod
    def test_proxy_passed_to_httpx_client() -> None:
        """A proxy is stored on the HTTPX transport."""
        proxy = "http://proxy.example:8080"
        transport = HTTPXTransport(proxy=proxy)
        assert transport.proxy == proxy
        transport.close()

    @staticmethod
    def test_limits_and_proxy_passed_to_httpx_client() -> None:
        """Limits and proxy can both be set on the HTTPX transport."""
        limits = httpx.Limits(max_connections=5)
        proxy = "http://proxy.example:8080"
        transport = HTTPXTransport(limits=limits, proxy=proxy)
        assert transport.limits is limits
        assert transport.proxy == proxy
        transport.close()

    @staticmethod
    def test_limits_and_timeout_passed_to_httpx_client() -> None:
        """Limits and timeout can both be set on the HTTPX transport."""
        limits = httpx.Limits(max_connections=5)
        timeout = httpx.Timeout(timeout=12.5)
        transport = HTTPXTransport(limits=limits, timeout=timeout)
        assert transport.limits is limits
        assert transport.timeout == timeout
        transport.close()


class TestHTTPX2Transport:
    """Tests for ``HTTPX2Transport``."""

    @staticmethod
    def test_is_transport() -> None:
        """HTTPX2Transport satisfies the Transport protocol."""
        with HTTPX2Transport() as transport:
            assert isinstance(transport, Transport)

    @staticmethod
    def test_httpx2_configuration_types() -> None:
        """HTTPX2 configuration objects are stored on the transport."""
        limits = httpx2.Limits(max_connections=5)
        proxy = httpx2.Proxy(url="http://proxy.example:8080")
        timeout = httpx2.Timeout(timeout=12.5)
        with HTTPX2Transport(
            limits=limits, proxy=proxy, timeout=timeout
        ) as transport:
            assert transport.limits is limits
            assert transport.proxy is proxy
            assert transport.timeout is timeout

    @staticmethod
    def test_real_httpx2_request(httpx2_mock: respx.Router) -> None:
        """The transport makes a request through an HTTPX2 client."""
        httpx2_mock.post(url="https://api.example/items").respond(
            status_code=HTTPStatus.CREATED,
            headers={"X-Family": "httpx2"},
            content=b"created",
        )

        with HTTPX2Transport() as transport:
            response = transport(
                method="POST",
                url="https://api.example/items",
                headers={"Authorization": "Token"},
                params={"page": 2},
                data=None,
                files=None,
                json={"name": "example"},
            )

        assert response == TransportResponse(
            status_code=HTTPStatus.CREATED,
            headers={
                "x-family": "httpx2",
                "content-length": "7",
            },
            content=b"created",
        )

    @staticmethod
    def test_httpx2_exception_family(httpx2_mock: respx.Router) -> None:
        """HTTPX2 transport exceptions propagate without conversion."""
        error = httpx2.ConnectError(message="HTTPX2 failed")
        httpx2_mock.get(url="https://api.example/failure").mock(
            side_effect=error
        )

        with (
            HTTPX2Transport() as transport,
            pytest.raises(expected_exception=httpx2.ConnectError),
        ):
            transport(
                method="GET",
                url="https://api.example/failure",
                headers={},
                params=None,
                data=None,
                files=None,
            )


class TestTransportResponse:
    """Tests for ``TransportResponse``."""

    @staticmethod
    def test_raise_for_status_error() -> None:
        """An error status code raises HTTPStatusError."""
        error_content = b"Not Found"
        response = TransportResponse(
            status_code=HTTPStatus.NOT_FOUND,
            headers={},
            content=error_content,
        )
        with pytest.raises(expected_exception=HTTPStatusError) as exc_info:
            response.raise_for_status()
        assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
        assert exc_info.value.content == error_content

    @staticmethod
    def test_raise_for_status_ok() -> None:
        """A success status code does not raise."""
        response = TransportResponse(
            status_code=HTTPStatus.OK,
            headers={},
            content=b"{}",
        )
        response.raise_for_status()


class TestExceptionHierarchy:
    """Tests for the custom exception hierarchy."""

    @staticmethod
    def test_bad_request() -> None:
        """A 400 response raises BadRequestError."""
        response = TransportResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            headers={},
            content=b"Bad Request",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, BadRequestError)
        assert exc.status_code == HTTPStatus.BAD_REQUEST
        assert exc.content == b"Bad Request"
        assert exc.response is response

    @staticmethod
    def test_authentication_error() -> None:
        """A 401 response raises AuthenticationError."""
        response = TransportResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={},
            content=b"Unauthorized",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, AuthenticationError)

    @staticmethod
    def test_forbidden_error() -> None:
        """A 403 response raises ForbiddenError."""
        response = TransportResponse(
            status_code=HTTPStatus.FORBIDDEN,
            headers={},
            content=b"Forbidden",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, ForbiddenError)

    @staticmethod
    def test_not_found_error() -> None:
        """A 404 response raises NotFoundError."""
        response = TransportResponse(
            status_code=HTTPStatus.NOT_FOUND,
            headers={},
            content=b"Not Found",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, NotFoundError)

    @staticmethod
    def test_rate_limit_error() -> None:
        """A 429 response raises RateLimitError."""
        response = TransportResponse(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            headers={},
            content=b"Too Many Requests",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, RateLimitError)

    @staticmethod
    def test_server_error() -> None:
        """A 500 response raises ServerError."""
        response = TransportResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            headers={},
            content=b"Internal Server Error",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, ServerError)

    @staticmethod
    def test_bad_gateway_error() -> None:
        """A 502 response raises BadGatewayError."""
        response = TransportResponse(
            status_code=HTTPStatus.BAD_GATEWAY,
            headers={},
            content=b"Bad Gateway",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, BadGatewayError)

    @staticmethod
    def test_service_unavailable_error() -> None:
        """A 503 response raises ServiceUnavailableError."""
        response = TransportResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            headers={},
            content=b"Service Unavailable",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, ServiceUnavailableError)

    @staticmethod
    def test_gateway_timeout_error() -> None:
        """A 504 response raises GatewayTimeoutError."""
        response = TransportResponse(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            headers={},
            content=b"Gateway Timeout",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, GatewayTimeoutError)

    @staticmethod
    def test_unmapped_status_code() -> None:
        """An unmapped status code raises CoderPadError."""
        response = TransportResponse(
            status_code=HTTPStatus.IM_A_TEAPOT,
            headers={},
            content=b"I'm a teapot",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, CoderPadError)
        assert not isinstance(
            exc,
            (
                BadRequestError,
                AuthenticationError,
                ForbiddenError,
                NotFoundError,
                RateLimitError,
                ServerError,
                BadGatewayError,
                ServiceUnavailableError,
                GatewayTimeoutError,
            ),
        )
        assert exc.status_code == HTTPStatus.IM_A_TEAPOT

    @staticmethod
    def test_nonstandard_status_code() -> None:
        """A non-standard status code raises CoderPadError."""
        nonstandard_status = 999
        response = TransportResponse(
            status_code=nonstandard_status,
            headers={},
            content=b"Unknown",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, CoderPadError)
        assert not isinstance(
            exc,
            (
                BadRequestError,
                AuthenticationError,
                ForbiddenError,
                NotFoundError,
                RateLimitError,
                ServerError,
                BadGatewayError,
                ServiceUnavailableError,
                GatewayTimeoutError,
            ),
        )
        assert exc.status_code == nonstandard_status

    @staticmethod
    def test_all_subclasses_are_coderpad_errors() -> None:
        """All specific exceptions are CoderPadError subclasses."""
        response = TransportResponse(
            status_code=HTTPStatus.NOT_FOUND,
            headers={},
            content=b"Not Found",
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, CoderPadError)

    @staticmethod
    def test_subclass_without_status_code() -> None:
        """A subclass without a status_code is not registered."""

        class _CustomError(CoderPadError):
            """A custom error without a mapped status code."""

        # Verify from_response never returns _CustomError for
        # any common status code.
        for code in (
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.NOT_FOUND,
            HTTPStatus.IM_A_TEAPOT,
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        ):
            response = TransportResponse(
                status_code=code,
                headers={},
                content=b"",
            )
            exc = CoderPadError.from_response(response=response)
            assert not isinstance(exc, _CustomError)

    @staticmethod
    def test_error_message() -> None:
        """The exception message includes the status code."""
        response = TransportResponse(
            status_code=HTTPStatus.NOT_FOUND,
            headers={},
            content=b"Not Found",
        )
        exc = CoderPadError.from_response(response=response)
        assert exc.args[0] == "HTTP 404"

    @staticmethod
    def test_parses_json_error_body() -> None:
        """JSON error bodies populate code and message attributes."""
        response = TransportResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={},
            content=b'{"code": "Unauthorized", "message": "Invalid API key"}',
        )
        exc = CoderPadError.from_response(response=response)
        assert isinstance(exc, AuthenticationError)
        assert exc.code == "Unauthorized"
        assert exc.message == "Invalid API key"

    @staticmethod
    def test_non_json_error_body_leaves_code_message_none() -> None:
        """Non-JSON bodies leave code and message as None."""
        response = TransportResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            headers={},
            content=b"not-json",
        )
        exc = CoderPadError.from_response(response=response)
        assert exc.code is None
        assert exc.message is None

    @staticmethod
    def test_non_object_json_error_body_leaves_code_message_none() -> None:
        """JSON arrays (non-objects) leave code and message as None."""
        response = TransportResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            headers={},
            content=b'["not", "an", "object"]',
        )
        exc = CoderPadError.from_response(response=response)
        assert exc.code is None
        assert exc.message is None

    @staticmethod
    def test_json_object_without_string_code_or_message() -> None:
        """JSON objects without string code/message leave them None."""
        response = TransportResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            headers={},
            content=b'{"code": 123, "message": null, "other": "x"}',
        )
        exc = CoderPadError.from_response(response=response)
        assert exc.code is None
        assert exc.message is None

    @staticmethod
    def test_client_raises_specific_exception() -> None:
        """The client raises specific exceptions for error responses."""

        def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return a 404 response."""
            del method, url, headers, params, data, files
            return TransportResponse(
                status_code=HTTPStatus.NOT_FOUND,
                headers={},
                content=b"Not Found",
            )

        client = CoderPad(
            api_key="test-key",
            transport=_error_transport,
        )
        with pytest.raises(expected_exception=NotFoundError):
            client.pads.get(pad_id="nonexistent")


class TestListPads:
    """Tests for ``CoderPad.pads.list``."""

    @staticmethod
    def test_list_pads_parses_prev_page() -> None:
        """Pads.list exposes prev_page when present in the API
        response.
        """

        class _Transport:
            """Return a pads page that includes prev_page."""

            def __call__(
                self,
                *,
                method: str,
                url: str,
                headers: dict[str, str],
                params: dict[str, str | int] | None,
                data: dict[str, str] | None,
                files: (dict[str, tuple[str, bytes, str]] | None),
            ) -> TransportResponse:
                """Return synthetic paginated pads JSON."""
                del method, url, headers, params, data, files
                payload: dict[str, object] = {
                    "status": "OK",
                    "pads": [],
                    "total": 0,
                    "next_page": "https://app.coderpad.io/api/pads?page=3",
                    "prev_page": "https://app.coderpad.io/api/pads?page=1",
                }
                return TransportResponse(
                    status_code=HTTPStatus.OK,
                    headers={},
                    content=json.dumps(obj=payload).encode(),
                )

        client = CoderPad(api_key="test-key", transport=_Transport())
        result = client.pads.list()
        assert result.prev_page == "https://app.coderpad.io/api/pads?page=1"
        assert result.next_page == "https://app.coderpad.io/api/pads?page=3"
        client.close()

    @staticmethod
    def test_list_pads(
        coderpad_client: CoderPad,
    ) -> None:
        """Pads can be listed."""
        result = coderpad_client.pads.list()
        assert result.total >= 0

    @staticmethod
    def test_list_pads_with_sort(
        coderpad_client: CoderPad,
    ) -> None:
        """Pads can be listed with a sort parameter."""
        result = coderpad_client.pads.list(
            sort=SortOrder.UPDATED_AT_DESC,
        )
        assert result.total >= 0

    @staticmethod
    def test_list_pads_with_page(
        coderpad_client: CoderPad,
    ) -> None:
        """Pads can be listed with a page parameter."""
        result = coderpad_client.pads.list(page=2)
        assert result.total >= 0


class TestCreatePad:
    """Tests for ``CoderPad.pads.create``."""

    @staticmethod
    def test_create_pad(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be created."""
        result = coderpad_client.pads.create(
            title="Test Pad",
            language="python",
        )
        assert result.id

    @staticmethod
    def test_create_pad_all_params(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be created with all parameters."""
        result = coderpad_client.pads.create(
            title="Test Pad",
            language="python",
            contents="print('hello')",
            notes="Private notes",
        )
        assert result.id

    @staticmethod
    def test_create_pad_minimal(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be created with no parameters."""
        result = coderpad_client.pads.create()
        assert result.id

    @staticmethod
    def test_create_pad_with_language_enum(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be created with a Language enum value."""
        result = coderpad_client.pads.create(
            title="Test Pad",
            language=Language.PYTHON,
        )
        assert result.id

    @staticmethod
    def test_create_pad_from_question(
        coderpad_client: CoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """A pad can be spawned from an existing question id."""
        result = coderpad_client.pads.create(question_id=54321)
        assert result.id
        request = mock_coderpad_api.calls.last.request
        assert b"question_id=54321" in request.content


class TestGetPad:
    """Tests for ``CoderPad.pads.get``."""

    @staticmethod
    def test_get_pad(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be retrieved by id."""
        result = coderpad_client.pads.get(
            pad_id="ABC1234",
        )
        assert result.id


class TestUpdatePad:
    """Tests for ``CoderPad.pads.update``."""

    @staticmethod
    def test_update_pad(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be updated."""
        coderpad_client.pads.update(
            pad_id="ABC1234",
            title="Updated Title",
        )

    @staticmethod
    def test_update_pad_no_title(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be updated without a title."""
        coderpad_client.pads.update(
            pad_id="ABC1234",
            language="python",
        )

    @staticmethod
    def test_update_pad_all_params(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad can be updated with all parameters."""
        coderpad_client.pads.update(
            pad_id="ABC1234",
            title="Updated Title",
            language="python",
            contents="print('hello')",
            notes="Notes",
            ended=True,
            deleted=False,
        )


class TestGetPadEvents:
    """Tests for ``CoderPad.pads.get_events``."""

    @staticmethod
    def test_get_pad_events(
        coderpad_client: CoderPad,
    ) -> None:
        """Pad events can be retrieved."""
        result = coderpad_client.pads.get_events(
            pad_id="ABC1234",
        )
        assert result.total >= 0

    @staticmethod
    def test_get_pad_events_with_params(
        coderpad_client: CoderPad,
    ) -> None:
        """Pad events can be retrieved with sort and page."""
        result = coderpad_client.pads.get_events(
            pad_id="ABC1234",
            sort=SortOrder.CREATED_AT_ASC,
            page=1,
        )
        assert result.total >= 0


class TestGetPadEnvironment:
    """Tests for ``CoderPad.pads.get_environment``."""

    @staticmethod
    def test_get_pad_environment(
        coderpad_client: CoderPad,
    ) -> None:
        """A pad environment can be retrieved."""
        result = coderpad_client.pads.get_environment(
            environment_id="123",
        )
        assert result.id

    @staticmethod
    def test_live_response_variants(
        live_variant_organization_id: int,
        live_variant_response: Callable[..., TransportResponse],
    ) -> None:
        """Undocumented environment and organization variants are
        supported.
        """

        def _transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return synthetic live-response variants."""
            del headers, params, data, files
            return live_variant_response(method=method, url=url)

        client = CoderPad(api_key="test-key", transport=_transport)
        environment = client.pads.get_environment(
            environment_id="binary",
        )
        assert environment.file_contents[0].contents is None
        assert environment.file_contents[0].binary is True

        organization = client.organization.get()
        assert organization.id == live_variant_organization_id
        assert organization.single_sign_in_url is None

        questions = [
            client.questions.get(question_id="custom"),
            client.questions.list()[0],
            client.questions.create(title="FizzBuzz", language="python"),
        ]
        assert all(
            question.ai_assist_custom_system_prompt == "Only provide hints."
            for question in questions
        )


class TestGetPadHistory:
    """Tests for ``CoderPad.pads.get_history``."""

    @staticmethod
    def test_get_history() -> None:
        """Editor history can be retrieved and replayed."""
        history_url = "https://coderpad-1.firebaseio.com/history.json"

        def _history_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return sample Firebase history."""
            del params, data, files
            assert method == "GET"
            assert url == history_url
            assert headers == {"Accept": "application/json"}
            return TransportResponse(
                status_code=HTTPStatus.OK,
                headers={},
                content=json.dumps(
                    obj={
                        "entry-1": {
                            "a": "author-1",
                            "o": ["hi"],
                            "t": 1,
                        },
                    },
                ).encode(),
            )

        client = CoderPad(
            api_key="test-key",
            transport=_history_transport,
        )
        history = client.pads.get_history(history_url=history_url)
        assert history.replay() == "hi"

    @staticmethod
    def test_get_empty_history() -> None:
        """A Firebase null response becomes an empty history."""

        def _empty_history_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return an empty Firebase history."""
            del method, url, headers, params, data, files
            return TransportResponse(
                status_code=HTTPStatus.OK,
                headers={},
                content=b"null",
            )

        client = CoderPad(
            api_key="test-key",
            transport=_empty_history_transport,
        )
        history = client.pads.get_history(
            history_url="https://example.com/history.json",
        )
        assert not history

    @staticmethod
    def test_get_history_error() -> None:
        """Firebase HTTP errors use the client exception hierarchy."""

        def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return a missing history response."""
            del method, url, headers, params, data, files
            return TransportResponse(
                status_code=HTTPStatus.NOT_FOUND,
                headers={},
                content=b"Not Found",
            )

        client = CoderPad(
            api_key="test-key",
            transport=_error_transport,
        )
        with pytest.raises(expected_exception=NotFoundError):
            client.pads.get_history(
                history_url="https://example.com/history.json",
            )


class TestListQuestions:
    """Tests for ``CoderPad.questions.list``."""

    @staticmethod
    def test_list_questions(
        coderpad_client: CoderPad,
    ) -> None:
        """Questions can be listed."""
        result = coderpad_client.questions.list()
        assert result.total >= 0
        assert (
            result[0].ai_assist_custom_system_prompt == "Only provide hints."
        )

    @staticmethod
    def test_list_questions_with_params(
        coderpad_client: CoderPad,
    ) -> None:
        """Questions can be listed with sort and page."""
        result = coderpad_client.questions.list(
            sort=SortOrder.UPDATED_AT_DESC,
            page=1,
        )
        assert result.total >= 0


class TestCreateQuestion:
    """Tests for ``CoderPad.questions.create``."""

    @staticmethod
    def test_create_question(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be created."""
        result = coderpad_client.questions.create(
            title="Test Question",
            language="python",
        )
        assert result.id
        assert result.ai_assist_custom_system_prompt == "Only provide hints."

    @staticmethod
    def test_create_question_all_params(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be created with all parameters."""
        result = coderpad_client.questions.create(
            title="Test Question",
            language="python",
            description="A description",
            contents="def solve(): pass",
            solution="def solve(): return 42",
            ai_assist_custom_system_prompt="Only provide hints.",
            candidate_instructions=[
                CandidateInstruction(
                    instructions="Part 1",
                    default_visible=True,
                ),
                CandidateInstruction(instructions="Part 2"),
            ],
        )
        assert result.id

    @staticmethod
    def test_create_question_with_language_enum(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be created with a Language enum."""
        result = coderpad_client.questions.create(
            title="Test Question",
            language=Language.PYTHON,
        )
        assert result.id

    @staticmethod
    def test_create_question_with_file_contents(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be created with file contents."""
        result = coderpad_client.questions.create(
            title="Multi-file Question",
            language=Language.MULTIFILE_PYTHON,
            file_contents=[
                QuestionFileContent(
                    path="main.py",
                    contents="print('hello')",
                ),
                QuestionFileContent(
                    path="lib/utils.py",
                    contents="def helper(): pass",
                ),
            ],
        )
        assert result.id

    @staticmethod
    def test_create_question_with_zip_file(
        coderpad_client: CoderPad,
        tmp_path: Path,
    ) -> None:
        """A question can be created with a zip file."""
        zip_path = tmp_path / "project.zip"
        zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        result = coderpad_client.questions.create(
            title="Zip Question",
            language=Language.MULTIFILE_JAVA,
            zip_file=zip_path,
        )
        assert result.id

    @staticmethod
    def test_create_question_candidate_instructions_body(
        coderpad_client: CoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Candidate instructions are serialized into the form body."""
        coderpad_client.questions.create(
            title="Live Question",
            language="python",
            ai_assist_custom_system_prompt="Only provide hints.",
            candidate_instructions=[
                CandidateInstruction(
                    instructions="Part 1",
                    default_visible=True,
                ),
                CandidateInstruction(instructions="Part 2"),
            ],
        )
        request = mock_coderpad_api.calls.last.request
        sent = parse_qs(qs=request.content.decode())
        assert sent["question[ai_assist_custom_system_prompt]"] == [
            "Only provide hints.",
        ]
        assert json.loads(
            s=sent["question[candidate_instructions]"][0],
        ) == [
            {"instructions": "Part 1", "default_visible": True},
            {"instructions": "Part 2", "default_visible": False},
        ]

    @staticmethod
    def test_create_question_rejects_multiple_content_sources(
        coderpad_client: CoderPad,
        tmp_path: Path,
    ) -> None:
        """Creating with multiple content sources raises ValueError."""
        zip_path = tmp_path / "project.zip"
        zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        with pytest.raises(
            expected_exception=ValueError,
            match="at most one of contents, file_contents, or zip_file",
        ):
            coderpad_client.questions.create(
                title="Conflict",
                language="python",
                contents="print(1)",
                file_contents=[
                    QuestionFileContent(path="main.py", contents="x"),
                ],
            )
        with pytest.raises(expected_exception=ValueError, match="zip_file"):
            coderpad_client.questions.create(
                title="Conflict",
                language="python",
                contents="print(1)",
                zip_file=zip_path,
            )


class TestGetQuestion:
    """Tests for ``CoderPad.questions.get``."""

    @staticmethod
    def test_get_question(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be retrieved by id."""
        result = coderpad_client.questions.get(
            question_id="123",
        )
        assert result.id
        assert result.ai_assist_custom_system_prompt == "Only provide hints."


class TestUpdateQuestion:
    """Tests for ``CoderPad.questions.update``."""

    @staticmethod
    def test_update_question(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be updated."""
        coderpad_client.questions.update(
            question_id="123",
            title="Updated Question",
        )

    @staticmethod
    def test_update_question_no_title(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be updated without a title."""
        coderpad_client.questions.update(
            question_id="123",
            language="ruby",
        )

    @staticmethod
    def test_update_question_all_params(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be updated with all parameters."""
        coderpad_client.questions.update(
            question_id="123",
            title="Updated",
            language="ruby",
            description="New desc",
            contents="puts 'hi'",
            solution="puts 'answer'",
            ai_assist_custom_system_prompt="Only provide hints.",
            candidate_instructions=[
                CandidateInstruction(
                    instructions="Part 1",
                    default_visible=True,
                ),
                CandidateInstruction(instructions="Part 2"),
            ],
        )

    @staticmethod
    def test_update_question_with_file_contents(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be updated with file contents."""
        coderpad_client.questions.update(
            question_id="123",
            file_contents=[
                QuestionFileContent(
                    path="main.py",
                    contents="print('updated')",
                ),
            ],
        )

    @staticmethod
    def test_update_question_with_zip_file(
        coderpad_client: CoderPad,
        tmp_path: Path,
    ) -> None:
        """A question can be updated with a zip file."""
        zip_path = tmp_path / "project.zip"
        zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        coderpad_client.questions.update(
            question_id="123",
            zip_file=zip_path,
        )

    @staticmethod
    def test_update_question_candidate_instructions_body(
        coderpad_client: CoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Candidate instructions are serialized into the form body."""
        coderpad_client.questions.update(
            question_id="123",
            candidate_instructions=[
                CandidateInstruction(
                    instructions="Part 1",
                    default_visible=True,
                ),
                CandidateInstruction(instructions="Part 2"),
            ],
        )
        request = mock_coderpad_api.calls.last.request
        sent = parse_qs(qs=request.content.decode())
        assert json.loads(
            s=sent["question[candidate_instructions]"][0],
        ) == [
            {"instructions": "Part 1", "default_visible": True},
            {"instructions": "Part 2", "default_visible": False},
        ]

    @staticmethod
    def test_update_question_ai_assist_system_prompt_body(
        coderpad_client: CoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """AI Assist's system prompt is serialized into the form body."""
        coderpad_client.questions.update(
            question_id="123",
            ai_assist_custom_system_prompt="Only provide hints.",
        )
        request = mock_coderpad_api.calls.last.request
        sent = parse_qs(qs=request.content.decode())
        assert sent["question[ai_assist_custom_system_prompt]"] == [
            "Only provide hints.",
        ]

    @staticmethod
    def test_update_question_rejects_multiple_content_sources(
        coderpad_client: CoderPad,
        tmp_path: Path,
    ) -> None:
        """Updating with multiple content sources raises ValueError."""
        zip_path = tmp_path / "project.zip"
        zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        with pytest.raises(expected_exception=ValueError, match="at most one"):
            coderpad_client.questions.update(
                question_id="1",
                contents="print(1)",
                zip_file=zip_path,
            )


class TestDeleteQuestion:
    """Tests for ``CoderPad.questions.delete``."""

    @staticmethod
    def test_delete_question(
        coderpad_client: CoderPad,
    ) -> None:
        """A question can be deleted."""
        coderpad_client.questions.delete(
            question_id="123",
        )


class TestGetQuota:
    """Tests for ``CoderPad.organization.get_quota``."""

    @staticmethod
    def test_get_quota(
        coderpad_client: CoderPad,
    ) -> None:
        """Quota information can be retrieved."""
        result = coderpad_client.organization.get_quota()
        assert result.pads_used >= 0


class TestGetOrganization:
    """Tests for ``CoderPad.organization.get``."""

    @staticmethod
    def test_get_organization(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization information can be retrieved."""
        result = coderpad_client.organization.get()
        assert result.organization_name


class TestGetOrganizationStats:
    """Tests for ``CoderPad.organization.get_stats``."""

    @staticmethod
    def test_get_organization_stats(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization stats can be retrieved."""
        result = coderpad_client.organization.get_stats()
        assert result.pads_created >= 0

    @staticmethod
    def test_get_organization_stats_with_params(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization stats can be filtered by time range."""
        result = coderpad_client.organization.get_stats(
            start_time="2023-07-01T00:00:00Z",
            end_time="2023-07-31T00:00:00Z",
        )
        assert result.pads_created >= 0


class TestListOrganizationPads:
    """Tests for ``CoderPad.organization.pads.list``."""

    @staticmethod
    def test_list_organization_pads(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization pads can be listed."""
        result = coderpad_client.organization.pads.list()
        assert result.total >= 0

    @staticmethod
    def test_list_organization_pads_with_params(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization pads can be listed with optional arguments."""
        result = coderpad_client.organization.pads.list(
            sort=SortOrder.UPDATED_AT_ASC,
            page=1,
        )
        assert result.total >= 0


class TestListOrganizationQuestions:
    """Tests for ``CoderPad.organization.questions.list``."""

    @staticmethod
    def test_list_organization_questions(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization questions can be listed."""
        result = coderpad_client.organization.questions.list()
        assert result.total >= 0
        assert (
            result[0].ai_assist_custom_system_prompt == "Only provide hints."
        )

    @staticmethod
    def test_list_organization_questions_with_params(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization questions can be listed with optional
        arguments.
        """
        result = coderpad_client.organization.questions.list(
            sort=SortOrder.CREATED_AT_DESC,
            page=1,
        )
        assert result.total >= 0


class TestListOrganizationUsers:
    """Tests for ``CoderPad.organization.users.list``."""

    @staticmethod
    def test_list_organization_users(
        coderpad_client: CoderPad,
    ) -> None:
        """Organization users can be listed and decoded."""
        result = coderpad_client.organization.users.list()
        assert result
        assert all(isinstance(item, OrganizationUser) for item in result)

    @staticmethod
    def test_list_organization_users_with_email(
        coderpad_client: CoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Organization users can be filtered by email."""
        email = "buddy@company.io"
        result = coderpad_client.organization.users.list(email=email)
        request = mock_coderpad_api.calls.last.request
        assert request.url.params["email"] == email
        assert all(isinstance(item, OrganizationUser) for item in result)

    @staticmethod
    def test_list_organization_users_empty() -> None:
        """An empty organization user response decodes to an empty
        list.
        """

        def _empty_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return an empty successful user response."""
            del method, url, headers, params, data, files
            return TransportResponse(
                status_code=HTTPStatus.OK,
                headers={},
                content=b'{"status": "OK", "users": []}',
            )

        client = CoderPad(api_key="test-key", transport=_empty_transport)
        assert client.organization.users.list() == []

    @staticmethod
    def test_list_organization_users_maps_http_errors() -> None:
        """Organization user HTTP failures use the client error
        hierarchy.
        """

        def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: dict[str, str | int] | None,
            data: dict[str, str] | None,
            files: (dict[str, tuple[str, bytes, str]] | None),
        ) -> TransportResponse:
            """Return a not-found user response."""
            del method, url, headers, params, data, files
            return TransportResponse(
                status_code=HTTPStatus.NOT_FOUND,
                headers={},
                content=b"Not Found",
            )

        client = CoderPad(api_key="test-key", transport=_error_transport)
        with pytest.raises(expected_exception=NotFoundError):
            client.organization.users.list()


class TestPadsAll:
    """Tests for ``PadsNamespace.all``."""

    @staticmethod
    def test_all_yields_pads_across_pages() -> None:
        """All() follows pagination until next_page is absent."""
        pad: dict[str, object] = {
            "id": "pad-1",
            "title": "One",
            "state": "active",
            "owner_email": "owner@example.com",
            "language": "python",
            "private": True,
            "execution_enabled": True,
            "contents": "",
            "participants": [],
            "events": "[]",
            "notes": "",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "ended_at": None,
            "url": "https://app.coderpad.io/pad-1",
            "playback": "https://app.coderpad.io/pad-1/playback",
            "history": None,
            "drawing": None,
            "type": "sandbox",
            "question_ids": [],
            "pad_environment_ids": [],
            "active_environment_id": None,
            "team": {"id": "team-1", "name": "Backend"},
            "restrict_interviewer_access": False,
        }
        pages: dict[int, dict[str, object]] = {
            1: {
                "status": "OK",
                "pads": [pad],
                "total": 2,
                "next_page": "https://app.coderpad.io/api/pads/?page=2",
            },
            2: {
                "status": "OK",
                "pads": [{**pad, "id": "pad-2", "title": "Two"}],
                "total": 2,
                "next_page": None,
            },
        }

        class _Transport:
            """Serve two pad pages keyed by page query param."""

            def __call__(
                self,
                *,
                method: str,
                url: str,
                headers: dict[str, str],
                params: dict[str, str | int] | None,
                data: dict[str, str] | None,
                files: (dict[str, tuple[str, bytes, str]] | None),
            ) -> TransportResponse:
                """Return the page matching the request."""
                del method, url, headers, data, files
                page_number = (
                    1 if params is None else int(params.get("page", 1))
                )
                return TransportResponse(
                    status_code=HTTPStatus.OK,
                    headers={},
                    content=json.dumps(obj=pages[page_number]).encode(),
                )

        client = CoderPad(api_key="test-key", transport=_Transport())
        titles = [item.title for item in client.pads.all()]
        assert titles == ["One", "Two"]
        client.close()
