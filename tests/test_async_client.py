"""Tests for the async CoderPad client."""

import json
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import httpx2
import pytest
import respx

from coderpad.async_client import AsyncCoderPad
from coderpad.exceptions import NotFoundError
from coderpad.transports import (
    AsyncHTTPX2Transport,
    AsyncHTTPXTransport,
    AsyncTransport,
    TransportResponse,
)
from coderpad.types import (
    CandidateInstruction,
    Language,
    OrganizationUser,
    QuestionFileContent,
    SortOrder,
)


class TestAsyncCoderPad:
    """Tests for ``AsyncCoderPad``."""

    @staticmethod
    def test_default_base_url() -> None:
        """The default base URL is the CoderPad app."""
        client = AsyncCoderPad(api_key="test-key")
        assert client.base_url == "https://app.coderpad.io"

    @staticmethod
    def test_custom_base_url() -> None:
        """A custom base URL can be provided."""
        client = AsyncCoderPad(
            api_key="test-key",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    @staticmethod
    @pytest.mark.asyncio
    async def test_custom_transport(
        mock_coderpad_api: object,
    ) -> None:
        """A custom transport can be provided."""
        del mock_coderpad_api
        transport = AsyncHTTPXTransport()
        client = AsyncCoderPad(
            api_key="test-key",
            transport=transport,
        )
        result = await client.pads.list()
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_mock_api_available(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """The mock API fixture provides a working mock."""
        result = await async_coderpad_client.pads.list()
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_aclose() -> None:
        """The client can be closed."""
        client = AsyncCoderPad(api_key="test-key")
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_async_context_manager() -> None:
        """The client can be used as an async context manager."""
        async with AsyncCoderPad(
            api_key="test-key",
        ) as client:
            assert isinstance(client, AsyncCoderPad)

    @staticmethod
    @pytest.mark.asyncio
    async def test_close_transport_without_aclose() -> None:
        """Closing works when transport has no aclose."""

        class _NoCloseTransport:
            """A transport without an aclose method."""

            async def __call__(
                self,
                *,
                method: str,
                url: str,
                headers: dict[str, str],
                params: (dict[str, str | int] | None),
                data: dict[str, str] | None,
                files: (dict[str, tuple[str, bytes, str]] | None),
            ) -> TransportResponse:  # pragma: no cover
                """Make a request."""
                raise NotImplementedError

        client = AsyncCoderPad(
            api_key="test-key",
            transport=_NoCloseTransport(),
        )
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_default_headers_merged_preserving_authorization() -> None:
        """Default headers merge while Authorization stays the API
        token.
        """
        client = AsyncCoderPad(
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
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_default_headers_merged_preserving_screen_api_key() -> None:
        """Default headers merge while Screen API-Key stays the Screen key."""
        client = AsyncCoderPad(
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
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_limits_forwarded_to_default_transport() -> None:
        """AsyncCoderPad forwards limits to the default transport."""
        limits = httpx.Limits(max_connections=10)
        client = AsyncCoderPad(api_key="test-key", limits=limits)
        transport = client.pads.transport
        assert isinstance(transport, AsyncHTTPXTransport)
        assert transport.limits is limits
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_timeout_forwarded_to_default_transport() -> None:
        """AsyncCoderPad forwards timeout to the default transport."""
        timeout = httpx.Timeout(timeout=7.5)
        client = AsyncCoderPad(api_key="test-key", timeout=timeout)
        transport = client.pads.transport
        assert isinstance(transport, AsyncHTTPXTransport)
        assert transport.timeout == timeout
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_proxy_forwarded_to_default_transport() -> None:
        """AsyncCoderPad forwards proxy to the default transport."""
        proxy = "http://proxy.example:8080"
        client = AsyncCoderPad(api_key="test-key", proxy=proxy)
        transport = client.pads.transport
        assert isinstance(transport, AsyncHTTPXTransport)
        assert transport.proxy == proxy
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
        """From_env loads Interview and Screen keys from the
        environment.
        """
        monkeypatch.setenv(name="CODERPAD_API_KEY", value="env-interview")
        monkeypatch.setenv(name="CODERPAD_SCREEN_API_KEY", value="env-screen")
        client = AsyncCoderPad.from_env()
        assert client.pads.headers["Authorization"] == (
            'Token token="env-interview"'
        )
        assert client.screen.headers["API-Key"] == "env-screen"
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_from_env_requires_api_key(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """From_env raises when CODERPAD_API_KEY is missing."""
        monkeypatch.delenv(name="CODERPAD_API_KEY", raising=False)
        monkeypatch.delenv(name="CODERPAD_SCREEN_API_KEY", raising=False)
        with pytest.raises(expected_exception=KeyError):
            _ = AsyncCoderPad.from_env()

    @staticmethod
    @pytest.mark.asyncio
    async def test_screen_lazy_requires_api_key() -> None:
        """Accessing screen without a Screen API key raises ValueError."""
        client = AsyncCoderPad(api_key="test-key")
        with pytest.raises(
            expected_exception=ValueError,
            match="screen_api_key",
        ):
            _ = client.screen
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_screen_lazy_initialized_once() -> None:
        """Screen namespace is created on first access and reused."""
        client = AsyncCoderPad(
            api_key="test-key",
            screen_api_key="screen-key",
        )
        first = client.screen
        second = client.screen
        assert first is second
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_screen_with_provided_transport() -> None:
        """Providing screen_transport closes that transport with the
        client.
        """
        transport = AsyncHTTPXTransport()
        client = AsyncCoderPad(
            api_key="test-key",
            screen_api_key="screen-key",
            screen_transport=transport,
        )
        assert client.screen.headers["API-Key"] == "screen-key"
        await client.aclose()


class TestAsyncHTTPXTransport:
    """Tests for ``AsyncHTTPXTransport``."""

    @staticmethod
    def test_is_async_transport() -> None:
        """AsyncHTTPXTransport satisfies AsyncTransport."""
        assert isinstance(
            AsyncHTTPXTransport(),
            AsyncTransport,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_aclose() -> None:
        """The transport can be closed."""
        transport = AsyncHTTPXTransport()
        await transport.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_async_context_manager() -> None:
        """The transport can be used as an async context manager."""
        async with AsyncHTTPXTransport() as transport:
            assert isinstance(
                transport,
                AsyncHTTPXTransport,
            )

    @staticmethod
    @pytest.mark.asyncio
    async def test_limits_passed_to_httpx_client() -> None:
        """Connection pool limits are stored on the async HTTPX
        transport.
        """
        limits = httpx.Limits(max_connections=5)
        transport = AsyncHTTPXTransport(limits=limits)
        assert transport.limits is limits
        await transport.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_timeout_passed_to_httpx_client() -> None:
        """A timeout is forwarded to the underlying async httpx client."""
        timeout = httpx.Timeout(timeout=12.5)
        transport = AsyncHTTPXTransport(timeout=timeout)
        assert transport.timeout == timeout
        await transport.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_proxy_passed_to_httpx_client() -> None:
        """A proxy is stored on the async HTTPX transport."""
        proxy = "http://proxy.example:8080"
        transport = AsyncHTTPXTransport(proxy=proxy)
        assert transport.proxy == proxy
        await transport.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_limits_and_proxy_passed_to_httpx_client() -> None:
        """Limits and proxy can both be set on the async HTTPX
        transport.
        """
        limits = httpx.Limits(max_connections=5)
        proxy = "http://proxy.example:8080"
        transport = AsyncHTTPXTransport(limits=limits, proxy=proxy)
        assert transport.limits is limits
        assert transport.proxy == proxy
        await transport.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_limits_and_timeout_passed_to_httpx_client() -> None:
        """Limits and timeout can both be set on the async HTTPX
        transport.
        """
        limits = httpx.Limits(max_connections=5)
        timeout = httpx.Timeout(timeout=12.5)
        transport = AsyncHTTPXTransport(limits=limits, timeout=timeout)
        assert transport.limits is limits
        assert transport.timeout == timeout
        await transport.aclose()


class TestAsyncHTTPX2Transport:
    """Tests for ``AsyncHTTPX2Transport``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_is_async_transport() -> None:
        """AsyncHTTPX2Transport satisfies AsyncTransport."""
        async with AsyncHTTPX2Transport() as transport:
            assert isinstance(transport, AsyncTransport)

    @staticmethod
    @pytest.mark.asyncio
    async def test_httpx2_configuration_types() -> None:
        """HTTPX2 configuration objects are stored on the transport."""
        limits = httpx2.Limits(max_connections=5)
        proxy = httpx2.Proxy(url="http://proxy.example:8080")
        timeout = httpx2.Timeout(timeout=12.5)
        async with AsyncHTTPX2Transport(
            limits=limits, proxy=proxy, timeout=timeout
        ) as transport:
            assert transport.limits is limits
            assert transport.proxy is proxy
            assert transport.timeout is timeout

    @staticmethod
    @pytest.mark.asyncio
    async def test_real_httpx2_request(httpx2_mock: respx.Router) -> None:
        """The transport makes a request through an HTTPX2 async
        client.
        """
        _ = httpx2_mock.get(url="https://api.example/items").respond(
            status_code=HTTPStatus.OK,
            headers={"X-Family": "httpx2"},
            content=b"listed",
        )

        async with AsyncHTTPX2Transport() as transport:
            response = await transport(
                method="GET",
                url="https://api.example/items",
                headers={"Authorization": "Token"},
                params={"page": 2},
                data=None,
                files=None,
            )

        assert response == TransportResponse(
            status_code=HTTPStatus.OK,
            headers={
                "x-family": "httpx2",
                "content-length": "6",
            },
            content=b"listed",
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_httpx2_exception_family(
        httpx2_mock: respx.Router,
    ) -> None:
        """HTTPX2 transport exceptions propagate without conversion."""
        error = httpx2.ConnectError(message="HTTPX2 failed")
        _ = httpx2_mock.get(url="https://api.example/failure").mock(
            side_effect=error
        )

        with pytest.raises(expected_exception=httpx2.ConnectError):
            async with AsyncHTTPX2Transport() as transport:
                await transport(
                    method="GET",
                    url="https://api.example/failure",
                    headers={},
                    params=None,
                    data=None,
                    files=None,
                )


class TestAsyncListPads:
    """Tests for ``AsyncCoderPad.pads.list``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_pads(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Pads can be listed."""
        result = await async_coderpad_client.pads.list()
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_pads_with_sort(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Pads can be listed with a sort parameter."""
        result = await async_coderpad_client.pads.list(
            sort=SortOrder.UPDATED_AT_DESC,
        )
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_pads_with_page(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Pads can be listed with a page parameter."""
        result = await async_coderpad_client.pads.list(
            page=2,
        )
        assert result.total >= 0


class TestAsyncCreatePad:
    """Tests for ``AsyncCoderPad.pads.create``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_pad(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be created."""
        result = await async_coderpad_client.pads.create(
            title="Test Pad",
            language="python",
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_pad_all_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be created with all parameters."""
        result = await async_coderpad_client.pads.create(
            title="Test Pad",
            language="python",
            contents="print('hello')",
            notes="Private notes",
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_pad_minimal(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be created with no parameters."""
        result = await async_coderpad_client.pads.create()
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_pad_with_language_enum(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be created with a Language enum value."""
        result = await async_coderpad_client.pads.create(
            title="Test Pad",
            language=Language.PYTHON,
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_pad_from_question(
        async_coderpad_client: AsyncCoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """A pad can be spawned from an existing question id."""
        result = await async_coderpad_client.pads.create(question_id=54321)
        assert bool(result.id)
        request = mock_coderpad_api.calls.last.request
        assert b"question_id=54321" in request.content


class TestAsyncGetPad:
    """Tests for ``AsyncCoderPad.pads.get``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_pad(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be retrieved by id."""
        result = await async_coderpad_client.pads.get(
            pad_id="ABC1234",
        )
        assert bool(result.id)


class TestAsyncUpdatePad:
    """Tests for ``AsyncCoderPad.pads.update``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_pad(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be updated."""
        await async_coderpad_client.pads.update(
            pad_id="ABC1234",
            title="Updated Title",
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_pad_no_title(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be updated without a title."""
        await async_coderpad_client.pads.update(
            pad_id="ABC1234",
            language="python",
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_pad_all_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad can be updated with all parameters."""
        await async_coderpad_client.pads.update(
            pad_id="ABC1234",
            title="Updated Title",
            language="python",
            contents="print('hello')",
            notes="Notes",
            ended=True,
            deleted=False,
        )


class TestAsyncGetPadEvents:
    """Tests for ``AsyncCoderPad.pads.get_events``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_pad_events(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Pad events can be retrieved."""
        result = await async_coderpad_client.pads.get_events(
            pad_id="ABC1234",
        )
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_pad_events_with_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Pad events can be retrieved with sort and page."""
        result = await async_coderpad_client.pads.get_events(
            pad_id="ABC1234",
            sort=SortOrder.CREATED_AT_ASC,
            page=1,
        )
        assert result.total >= 0


class TestAsyncGetPadEnvironment:
    """Tests for ``AsyncCoderPad.pads.get_environment``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_pad_environment(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A pad environment can be retrieved."""
        result = await async_coderpad_client.pads.get_environment(
            environment_id="123",
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_live_response_variants(
        live_variant_organization_id: int,
        live_variant_response: Callable[..., TransportResponse],
    ) -> None:
        """Undocumented environment and organization variants are
        supported.
        """

        async def _transport(
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

        client = AsyncCoderPad(api_key="test-key", transport=_transport)
        environment = await client.pads.get_environment(
            environment_id="binary",
        )
        assert environment.file_contents[0].contents is None
        assert environment.file_contents[0].binary is True

        organization = await client.organization.get()
        assert organization.id == live_variant_organization_id
        assert organization.single_sign_in_url is None

        questions = [
            await client.questions.get(question_id="custom"),
            (await client.questions.list())[0],
            await client.questions.create(
                title="FizzBuzz",
                language="python",
            ),
        ]
        assert all(
            question.ai_assist_custom_system_prompt == "Only provide hints."
            for question in questions
        )


class TestAsyncGetPadHistory:
    """Tests for ``AsyncCoderPad.pads.get_history``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_history() -> None:
        """Editor history can be retrieved and replayed."""
        history_url = "https://coderpad-1.firebaseio.com/history.json"

        async def _history_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(
            api_key="test-key",
            transport=_history_transport,
        )
        history = await client.pads.get_history(history_url=history_url)
        assert history.replay() == "hi"

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_empty_history() -> None:
        """A Firebase null response becomes an empty history."""

        async def _empty_history_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(
            api_key="test-key",
            transport=_empty_history_transport,
        )
        history = await client.pads.get_history(
            history_url="https://example.com/history.json",
        )
        assert not bool(history)

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_history_error() -> None:
        """Firebase HTTP errors use the client exception hierarchy."""

        async def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(
            api_key="test-key",
            transport=_error_transport,
        )
        with pytest.raises(expected_exception=NotFoundError):
            await client.pads.get_history(
                history_url="https://example.com/history.json",
            )


class TestAsyncListQuestions:
    """Tests for ``AsyncCoderPad.questions.list``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_questions(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Questions can be listed."""
        result = await async_coderpad_client.questions.list()
        assert result.total >= 0
        assert (
            result[0].ai_assist_custom_system_prompt == "Only provide hints."
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_questions_with_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Questions can be listed with sort and page."""
        result = await async_coderpad_client.questions.list(
            sort=SortOrder.UPDATED_AT_DESC,
            page=1,
        )
        assert result.total >= 0


class TestAsyncCreateQuestion:
    """Tests for ``AsyncCoderPad.questions.create``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be created."""
        result = await async_coderpad_client.questions.create(
            title="Test Question",
            language="python",
        )
        assert bool(result.id)
        assert result.ai_assist_custom_system_prompt == "Only provide hints."

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question_all_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be created with all parameters."""
        result = await async_coderpad_client.questions.create(
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
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question_with_language_enum(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be created with a Language enum."""
        result = await async_coderpad_client.questions.create(
            title="Test Question",
            language=Language.PYTHON,
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question_with_file_contents(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be created with file contents."""
        result = await async_coderpad_client.questions.create(
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
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question_with_zip_file(
        async_coderpad_client: AsyncCoderPad,
        tmp_path: Path,
    ) -> None:
        """A question can be created with a zip file."""
        zip_path = tmp_path / "project.zip"
        _ = zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        result = await async_coderpad_client.questions.create(
            title="Zip Question",
            language=Language.MULTIFILE_JAVA,
            zip_file=zip_path,
        )
        assert bool(result.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_question_candidate_instructions_body(
        async_coderpad_client: AsyncCoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Candidate instructions are serialized into the form body."""
        await async_coderpad_client.questions.create(
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
    @pytest.mark.asyncio
    async def test_create_question_rejects_multiple_content_sources(
        async_coderpad_client: AsyncCoderPad,
        tmp_path: Path,
    ) -> None:
        """Creating with multiple content sources raises ValueError."""
        zip_path = tmp_path / "project.zip"
        _ = zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        with pytest.raises(
            expected_exception=ValueError,
            match="at most one of contents, file_contents, or zip_file",
        ):
            await async_coderpad_client.questions.create(
                title="Conflict",
                language="python",
                contents="print(1)",
                file_contents=[
                    QuestionFileContent(path="main.py", contents="x"),
                ],
            )
        with pytest.raises(expected_exception=ValueError, match="zip_file"):
            await async_coderpad_client.questions.create(
                title="Conflict",
                language="python",
                contents="print(1)",
                zip_file=zip_path,
            )


class TestAsyncGetQuestion:
    """Tests for ``AsyncCoderPad.questions.get``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_question(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be retrieved by id."""
        result = await async_coderpad_client.questions.get(
            question_id="123",
        )
        assert bool(result.id)
        assert result.ai_assist_custom_system_prompt == "Only provide hints."


class TestAsyncUpdateQuestion:
    """Tests for ``AsyncCoderPad.questions.update``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be updated."""
        await async_coderpad_client.questions.update(
            question_id="123",
            title="Updated Question",
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question_no_title(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be updated without a title."""
        await async_coderpad_client.questions.update(
            question_id="123",
            language="ruby",
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question_all_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be updated with all params."""
        await async_coderpad_client.questions.update(
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
    @pytest.mark.asyncio
    async def test_update_question_with_file_contents(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be updated with file contents."""
        await async_coderpad_client.questions.update(
            question_id="123",
            file_contents=[
                QuestionFileContent(
                    path="main.py",
                    contents="print('updated')",
                ),
            ],
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question_with_zip_file(
        async_coderpad_client: AsyncCoderPad,
        tmp_path: Path,
    ) -> None:
        """A question can be updated with a zip file."""
        zip_path = tmp_path / "project.zip"
        _ = zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        await async_coderpad_client.questions.update(
            question_id="123",
            zip_file=zip_path,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question_candidate_instructions_body(
        async_coderpad_client: AsyncCoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Candidate instructions are serialized into the form body."""
        await async_coderpad_client.questions.update(
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
    @pytest.mark.asyncio
    async def test_update_question_ai_assist_system_prompt_body(
        async_coderpad_client: AsyncCoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """AI Assist's system prompt is serialized into the form body."""
        await async_coderpad_client.questions.update(
            question_id="123",
            ai_assist_custom_system_prompt="Only provide hints.",
        )
        request = mock_coderpad_api.calls.last.request
        sent = parse_qs(qs=request.content.decode())
        assert sent["question[ai_assist_custom_system_prompt]"] == [
            "Only provide hints.",
        ]

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_question_rejects_multiple_content_sources(
        async_coderpad_client: AsyncCoderPad,
        tmp_path: Path,
    ) -> None:
        """Updating with multiple content sources raises ValueError."""
        zip_path = tmp_path / "project.zip"
        _ = zip_path.write_bytes(data=b"PK\x03\x04fake-zip")
        with pytest.raises(expected_exception=ValueError, match="at most one"):
            await async_coderpad_client.questions.update(
                question_id="1",
                contents="print(1)",
                zip_file=zip_path,
            )


class TestAsyncDeleteQuestion:
    """Tests for ``AsyncCoderPad.questions.delete``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_question(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """A question can be deleted."""
        await async_coderpad_client.questions.delete(
            question_id="123",
        )


class TestAsyncGetQuota:
    """Tests for ``AsyncCoderPad.organization.get_quota``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_quota(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Quota information can be retrieved."""
        result = await async_coderpad_client.organization.get_quota()
        assert result.pads_used >= 0


class TestAsyncGetOrganization:
    """Tests for ``AsyncCoderPad.organization.get``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_organization(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization information can be retrieved."""
        result = await async_coderpad_client.organization.get()
        assert bool(result.organization_name)


class TestAsyncGetOrganizationStats:
    """Tests for ``AsyncCoderPad.organization.get_stats``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_organization_stats(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization stats can be retrieved."""
        result = await async_coderpad_client.organization.get_stats()
        assert result.pads_created >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_organization_stats_with_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization stats can be filtered by time."""
        result = await async_coderpad_client.organization.get_stats(
            start_time="2023-07-01T00:00:00Z",
            end_time="2023-07-31T00:00:00Z",
        )
        assert result.pads_created >= 0


class TestAsyncListOrganizationPads:
    """Tests for organization pads list."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_pads(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization pads can be listed."""
        result = await async_coderpad_client.organization.pads.list()
        assert result.total >= 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_pads_with_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization pads can be listed with optional arguments."""
        result = await async_coderpad_client.organization.pads.list(
            sort=SortOrder.UPDATED_AT_ASC,
            page=1,
        )
        assert result.total >= 0


class TestAsyncListOrganizationQuestions:
    """Tests for organization questions list."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_questions(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization questions can be listed."""
        result = await async_coderpad_client.organization.questions.list()
        assert result.total >= 0
        assert (
            result[0].ai_assist_custom_system_prompt == "Only provide hints."
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_org_questions_with_params(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization questions can be listed with optional
        arguments.
        """
        result = await async_coderpad_client.organization.questions.list(
            sort=SortOrder.CREATED_AT_DESC,
            page=1,
        )
        assert result.total >= 0


class TestAsyncListOrganizationUsers:
    """Tests for ``AsyncCoderPad.organization.users.list``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_users(
        async_coderpad_client: AsyncCoderPad,
    ) -> None:
        """Organization users can be listed and decoded."""
        result = await async_coderpad_client.organization.users.list()
        assert bool(result)
        assert all(isinstance(item, OrganizationUser) for item in result)

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_users_with_email(
        async_coderpad_client: AsyncCoderPad,
        mock_coderpad_api: respx.MockRouter,
    ) -> None:
        """Organization users can be filtered by email."""
        email = "buddy@company.io"
        result = await async_coderpad_client.organization.users.list(
            email=email,
        )
        request = mock_coderpad_api.calls.last.request
        assert request.url.params["email"] == email
        assert all(isinstance(item, OrganizationUser) for item in result)

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_users_empty() -> None:
        """An empty organization user response decodes to an empty
        list.
        """

        async def _empty_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(api_key="test-key", transport=_empty_transport)
        assert await client.organization.users.list() == []

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_organization_users_maps_http_errors() -> None:
        """Organization user HTTP failures use the client error
        hierarchy.
        """

        async def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(api_key="test-key", transport=_error_transport)
        with pytest.raises(expected_exception=NotFoundError):
            await client.organization.users.list()


class TestAsyncExceptionHandling:
    """Tests for async exception handling."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_client_raises_specific_exception() -> None:
        """The async client raises specific exceptions."""

        async def _error_transport(
            *,
            method: str,
            url: str,
            headers: dict[str, str],
            params: (dict[str, str | int] | None),
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

        client = AsyncCoderPad(
            api_key="test-key",
            transport=_error_transport,
        )
        with pytest.raises(
            expected_exception=NotFoundError,
        ):
            await client.pads.get(pad_id="nonexistent")


class TestAsyncPadsAll:
    """Tests for ``AsyncPadsNamespace.all``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_all_yields_pads_across_pages() -> None:
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

            async def __call__(
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

        client = AsyncCoderPad(api_key="test-key", transport=_Transport())
        titles = [item.title async for item in client.pads.all()]
        assert titles == ["One", "Two"]
        await client.aclose()
