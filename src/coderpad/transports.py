"""Transport abstractions for the CoderPad Interview API."""

import json as json_module
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Protocol, Self, TypedDict, runtime_checkable

import httpx
import httpx2
from beartype import beartype


class _HTTPXClientKwargs(TypedDict, total=False):
    """Optional kwargs forwarded to ``httpx.Client`` / ``AsyncClient``."""

    limits: httpx.Limits
    proxy: str | httpx.Proxy
    timeout: httpx.Timeout | float


class _HTTPX2ClientKwargs(TypedDict, total=False):
    """Optional kwargs forwarded to ``httpx2.Client`` /
    ``AsyncClient``.
    """

    limits: httpx2.Limits
    proxy: str | httpx2.Proxy
    timeout: httpx2.Timeout | float


class HTTPStatusError(Exception):
    """Raised when an HTTP response has an error status code."""

    def __init__(
        self,
        *,
        status_code: int,
        content: bytes,
    ) -> None:
        """Create a new HTTP status error.

        Args:
            status_code: The HTTP status code.
            content: The response body.
        """
        message = f"HTTP {status_code}"
        super().__init__(message)
        self.status_code = status_code
        self.content = content


@beartype
@dataclass(frozen=True, kw_only=True)
class TransportResponse:
    """A response from a transport."""

    status_code: int
    headers: dict[str, str]
    content: bytes

    def json(self) -> Any:  # noqa: ANN401
        """Parse the response body as JSON.

        Returns:
            The parsed JSON data.
        """
        return json_module.loads(s=self.content)

    def raise_for_status(self) -> None:
        """Raise an error if the response has an error status.

        Raises:
            HTTPStatusError: If the status code is 400 or above.
        """
        if self.status_code >= HTTPStatus.BAD_REQUEST:
            raise HTTPStatusError(
                status_code=self.status_code,
                content=self.content,
            )


@runtime_checkable
class Transport(Protocol):
    """Protocol for HTTP transports.

    A transport is a callable that makes an HTTP request and
    returns a ``TransportResponse``.
    """

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
        """Make an HTTP request.

        Args:
            method: The HTTP method (e.g. ``GET``, ``POST``).
            url: The full URL to request.
            headers: Headers to send with the request.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
                Each key is the field name, and the value is
                a ``(filename, content, content_type)`` tuple.

        Returns:
            A ``TransportResponse`` populated from the HTTP
            response.
        """
        ...  # pylint: disable=unnecessary-ellipsis


@runtime_checkable
class JSONTransport(Protocol):
    """Protocol for transports supporting JSON request bodies."""

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None,
    ) -> TransportResponse:
        """Make an HTTP request with an optional JSON body."""
        ...  # pylint: disable=unnecessary-ellipsis


@beartype
class HTTPXTransport:
    """HTTP transport using the ``httpx`` library.

    This is the default transport. It uses a shared
    ``httpx.Client`` for connection pooling.
    """

    def __init__(
        self,
        *,
        limits: httpx.Limits | None = None,
        proxy: str | httpx.Proxy | None = None,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        """Create a new HTTPX transport.

        Args:
            limits: Optional connection pool limits for ``httpx.Client``.
            proxy: Optional proxy passed to ``httpx.Client``.
            timeout: Optional timeout passed to ``httpx.Client``.
                When omitted, the default ``httpx`` timeout is used.
        """
        self.limits = limits
        self.proxy = proxy
        self.timeout = timeout
        client_kwargs: _HTTPXClientKwargs = {}
        if limits is not None:
            client_kwargs["limits"] = limits
        if proxy is not None:
            client_kwargs["proxy"] = proxy
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        self._client = httpx.Client(**client_kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter the context manager.

        Returns:
            This transport instance.
        """
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
    ) -> None:
        """Exit the context manager and close the client."""
        self.close()

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None = None,
    ) -> TransportResponse:
        """Make an HTTP request using ``httpx``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
            json: A JSON-compatible request body.

        Returns:
            A ``TransportResponse`` populated from the httpx
            response.
        """
        response = self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            files=files,
            json=json,
        )
        return TransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )


@beartype
class HTTPX2Transport:
    """HTTP transport using the ``httpx2`` library.

    This transport uses a shared ``httpx2.Client`` for connection pooling.
    Configuration objects must come from ``httpx2``, not ``httpx``.
    """

    def __init__(
        self,
        *,
        limits: httpx2.Limits | None = None,
        proxy: str | httpx2.Proxy | None = None,
        timeout: httpx2.Timeout | float | None = None,
    ) -> None:
        """Create a new HTTPX2 transport.

        Args:
            limits: Optional connection pool limits for ``httpx2.Client``.
            proxy: Optional proxy passed to ``httpx2.Client``.
            timeout: Optional timeout passed to ``httpx2.Client``.
                When omitted, the default ``httpx2`` timeout is used.
        """
        self.limits = limits
        self.proxy = proxy
        self.timeout = timeout
        client_kwargs: _HTTPX2ClientKwargs = {}
        if limits is not None:
            client_kwargs["limits"] = limits
        if proxy is not None:
            client_kwargs["proxy"] = proxy
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        self._client = httpx2.Client(**client_kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter the context manager.

        Returns:
            This transport instance.
        """
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
    ) -> None:
        """Exit the context manager and close the client."""
        self.close()

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None = None,
    ) -> TransportResponse:
        """Make an HTTP request using ``httpx2``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
            json: A JSON-compatible request body.

        Returns:
            A ``TransportResponse`` populated from the HTTPX2 response.
        """
        response = self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            files=files,
            json=json,
        )
        return TransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )


@runtime_checkable
class AsyncTransport(Protocol):
    """Protocol for async HTTP transports.

    An async transport is a callable that makes an async HTTP
    request and returns a ``TransportResponse``.
    """

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
        """Make an async HTTP request.

        Args:
            method: The HTTP method (e.g. ``GET``, ``POST``).
            url: The full URL to request.
            headers: Headers to send with the request.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
                Each key is the field name, and the value is
                a ``(filename, content, content_type)`` tuple.

        Returns:
            A ``TransportResponse`` populated from the HTTP
            response.
        """
        ...  # pylint: disable=unnecessary-ellipsis


@runtime_checkable
class AsyncJSONTransport(Protocol):
    """Protocol for async transports supporting JSON request bodies."""

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None,
    ) -> TransportResponse:
        """Make an async HTTP request with an optional JSON body."""
        ...  # pylint: disable=unnecessary-ellipsis


@beartype
class AsyncHTTPXTransport:
    """Async HTTP transport using the ``httpx`` library.

    This is the default async transport. It uses a shared
    ``httpx.AsyncClient`` for connection pooling.
    """

    def __init__(
        self,
        *,
        limits: httpx.Limits | None = None,
        proxy: str | httpx.Proxy | None = None,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        """Create a new async HTTPX transport.

        Args:
            limits: Optional connection pool limits for ``httpx.AsyncClient``.
            proxy: Optional proxy passed to ``httpx.AsyncClient``.
            timeout: Optional timeout passed to ``httpx.AsyncClient``.
                When omitted, the default ``httpx`` timeout is used.
        """
        self.limits = limits
        self.proxy = proxy
        self.timeout = timeout
        client_kwargs: _HTTPXClientKwargs = {}
        if limits is not None:
            client_kwargs["limits"] = limits
        if proxy is not None:
            client_kwargs["proxy"] = proxy
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        self._client = httpx.AsyncClient(**client_kwargs)

    async def aclose(self) -> None:
        """Close the underlying async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            This transport instance.
        """
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
        /,
    ) -> None:
        """Exit the async context manager and close."""
        await self.aclose()

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None = None,
    ) -> TransportResponse:
        """Make an async HTTP request using ``httpx``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
            json: A JSON-compatible request body.

        Returns:
            A ``TransportResponse`` populated from the httpx
            response.
        """
        response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            files=files,
            json=json,
        )
        return TransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )


@beartype
class AsyncHTTPX2Transport:
    """Async HTTP transport using the ``httpx2`` library.

    This transport uses a shared ``httpx2.AsyncClient`` for connection
    pooling. Configuration objects must come from ``httpx2``, not ``httpx``.
    """

    def __init__(
        self,
        *,
        limits: httpx2.Limits | None = None,
        proxy: str | httpx2.Proxy | None = None,
        timeout: httpx2.Timeout | float | None = None,
    ) -> None:
        """Create a new asynchronous HTTPX2 transport.

        Args:
            limits: Optional connection pool limits for ``httpx2.AsyncClient``.
            proxy: Optional proxy passed to ``httpx2.AsyncClient``.
            timeout: Optional timeout passed to ``httpx2.AsyncClient``.
                When omitted, the default ``httpx2`` timeout is used.
        """
        self.limits = limits
        self.proxy = proxy
        self.timeout = timeout
        client_kwargs: _HTTPX2ClientKwargs = {}
        if limits is not None:
            client_kwargs["limits"] = limits
        if proxy is not None:
            client_kwargs["proxy"] = proxy
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        self._client = httpx2.AsyncClient(**client_kwargs)

    async def aclose(self) -> None:
        """Close the underlying asynchronous HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            This transport instance.
        """
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
        /,
    ) -> None:
        """Exit the async context manager and close."""
        await self.aclose()

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
        json: object | None = None,
    ) -> TransportResponse:
        """Make an asynchronous HTTP request using ``httpx2``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            params: Query parameters.
            data: Form data to send in the request body.
            files: Files to upload as multipart form data.
            json: A JSON-compatible request body.

        Returns:
            A ``TransportResponse`` populated from the HTTPX2 response.
        """
        response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            files=files,
            json=json,
        )
        return TransportResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )
