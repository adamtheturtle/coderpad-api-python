"""Async CoderPad Interview API client."""

import builtins
import json
import os
from collections.abc import AsyncIterator, Sequence
from http import HTTPStatus
from pathlib import Path
from typing import Self

import httpx
from beartype import beartype

from coderpad._question_content import (
    validate_mutually_exclusive_question_content,
)
from coderpad.async_screen import AsyncScreenNamespace
from coderpad.exceptions import CoderPadError
from coderpad.screen import SCREEN_US_BASE_URL
from coderpad.transports import (
    AsyncHTTPX2Transport,
    AsyncHTTPXTransport,
    AsyncJSONTransport,
    AsyncTransport,
    TransportResponse,
)
from coderpad.types import (
    CandidateInstruction,
    Language,
    Organization,
    OrganizationStats,
    OrganizationUser,
    Pad,
    PadEnvironment,
    PadEvent,
    PadHistory,
    PaginatedList,
    Question,
    QuestionFileContent,
    Quota,
    SortOrder,
)


@beartype
class _AsyncNamespace:
    """Base class providing shared async request logic."""

    def __init__(
        self,
        *,
        transport: AsyncTransport,
        base_url: str,
        headers: dict[str, str],
    ) -> None:
        """Create a new async namespace.

        Args:
            transport: The async HTTP transport.
            base_url: The base URL for the API.
            headers: Headers to send with every request.
        """
        self.transport = transport
        self.base_url = base_url
        self.headers = headers

    async def _request(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        files: (dict[str, tuple[str, bytes, str]] | None),
    ) -> TransportResponse:
        """Make an async HTTP request.

        Args:
            method: The HTTP method.
            url: The URL path.
            params: Query parameters.
            data: Form data.
            files: Files to upload as multipart form data.

        Returns:
            The transport response.

        Raises:
            CoderPadError: If the response has an error
                status code.
        """
        response = await self.transport(
            method=method,
            url=self.base_url + url,
            headers=self.headers,
            params=params,
            data=data,
            files=files,
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise CoderPadError.from_response(response=response)
        return response


@beartype
class AsyncPadsNamespace(_AsyncNamespace):
    """Namespace for async pad operations."""

    async def list(
        self,
        *,
        sort: SortOrder | None = None,
        page: int | None = None,
    ) -> PaginatedList[Pad]:
        """Retrieve a list of pads.

        Args:
            sort: Sort order.
            page: Page number for pagination.

        Returns:
            The list of pads with pagination metadata.
        """
        params: dict[str, str | int] = {}
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        response = await self._request(
            method="GET",
            url="/api/pads/",
            params=params,
            data=None,
            files=None,
        )
        data = response.json()
        return PaginatedList(
            [Pad.from_dict(data=item) for item in data["pads"]],
            total=data["total"],
            next_page=data.get("next_page"),
            prev_page=data.get("prev_page"),
        )

    async def all(
        self,
        *,
        sort: SortOrder | None = None,
    ) -> AsyncIterator[Pad]:
        """Yield all pads across paginated responses.

        Args:
            sort: Sort order.

        Yields:
            Each pad from successive pages until ``next_page`` is absent.
        """
        page_number = 1
        while True:
            page = await self.list(sort=sort, page=page_number)
            for pad in page:
                yield pad
            if page.next_page is None:
                break
            page_number += 1

    async def create(
        self,
        *,
        title: str | None = None,
        language: Language | str | None = None,
        contents: str | None = None,
        notes: str | None = None,
        question_id: str | int | None = None,
    ) -> Pad:
        """Create a new pad.

        Args:
            title: Title for the pad.
            language: Programming language for the pad.
            contents: Initial contents of the pad editor.
            notes: Private notes for the interviewer.
            question_id: Id of an existing question to seed
                the pad from.

        Returns:
            The created pad.
        """
        data: dict[str, str] = {}
        if title is not None:
            data["title"] = title
        if language is not None:
            lang = language
            data["language"] = lang
        if contents is not None:
            data["contents"] = contents
        if notes is not None:
            data["notes"] = notes
        if question_id is not None:
            data["question_id"] = str(object=question_id)
        response = await self._request(
            method="POST",
            url="/api/pads/",
            data=data,
            params=None,
            files=None,
        )
        return Pad.from_dict(data=response.json())

    async def get(self, *, pad_id: str) -> Pad:
        """Retrieve a pad by id.

        Args:
            pad_id: The id of the pad.

        Returns:
            The pad.
        """
        response = await self._request(
            method="GET",
            url=f"/api/pads/{pad_id}",
            params=None,
            data=None,
            files=None,
        )
        return Pad.from_dict(data=response.json())

    async def update(
        self,
        *,
        pad_id: str,
        title: str | None = None,
        language: Language | str | None = None,
        contents: str | None = None,
        notes: str | None = None,
        ended: bool | None = None,
        deleted: bool | None = None,
    ) -> None:
        """Modify an existing pad.

        Args:
            pad_id: The id of the pad.
            title: New title for the pad.
            language: New programming language.
            contents: New contents of the pad editor.
            notes: New private notes.
            ended: Set to ``True`` to end the interview.
            deleted: Set to ``True`` to delete the pad.
        """
        data: dict[str, str] = {}
        if title is not None:
            data["title"] = title
        if language is not None:
            lang = language
            data["language"] = lang
        if contents is not None:
            data["contents"] = contents
        if notes is not None:
            data["notes"] = notes
        if ended is not None:
            data["ended"] = "true" if ended else "false"
        if deleted is not None:
            data["deleted"] = "true" if deleted else "false"
        await self._request(
            method="PUT",
            url=f"/api/pads/{pad_id}",
            data=data,
            params=None,
            files=None,
        )

    async def get_events(
        self,
        *,
        pad_id: str,
        sort: SortOrder | None = None,
        page: int | None = None,
    ) -> PaginatedList[PadEvent]:
        """Retrieve a list of pad events.

        Args:
            pad_id: The id of the pad.
            sort: Sort order.
            page: Page number for pagination.

        Returns:
            The list of pad events with pagination
            metadata.
        """
        params: dict[str, str | int] = {}
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        response = await self._request(
            method="GET",
            url=f"/api/pads/{pad_id}/events",
            params=params,
            data=None,
            files=None,
        )
        data = response.json()
        return PaginatedList(
            [PadEvent.model_validate(obj=item) for item in data["events"]],
            total=data["total"],
            next_page=data.get("next_page"),
            prev_page=data.get("prev_page"),
        )

    async def get_environment(
        self,
        *,
        environment_id: str,
    ) -> PadEnvironment:
        """Retrieve pad environment information.

        Args:
            environment_id: The id of the pad environment.

        Returns:
            The pad environment.
        """
        response = await self._request(
            method="GET",
            url=f"/api/pad_environments/{environment_id}",
            params=None,
            data=None,
            files=None,
        )
        return PadEnvironment.from_dict(
            data=response.json(),
        )

    async def get_history(self, *, history_url: str) -> PadHistory:
        """Retrieve editor history from a Firebase history URL.

        The URL is available as ``FileContent.history``. The CoderPad
        API key is deliberately not sent to the Firebase host.

        Args:
            history_url: The history URL returned for a file in a pad
                environment.

        Returns:
            The chronologically ordered editor history. An empty
            history is returned when Firebase responds with ``null``.
        """
        response = await self.transport(
            method="GET",
            url=history_url,
            headers={"Accept": "application/json"},
            params=None,
            data=None,
            files=None,
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise CoderPadError.from_response(response=response)
        data = response.json()
        if data is None:
            return PadHistory()
        return PadHistory.from_dict(data=data)


@beartype
class AsyncQuestionsNamespace(_AsyncNamespace):
    """Namespace for async question operations."""

    async def list(
        self,
        *,
        sort: SortOrder | None = None,
        page: int | None = None,
    ) -> PaginatedList[Question]:
        """Retrieve a list of questions.

        Args:
            sort: Sort order.
            page: Page number for pagination.

        Returns:
            The list of questions with pagination
            metadata.
        """
        params: dict[str, str | int] = {}
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        response = await self._request(
            method="GET",
            url="/api/questions/",
            params=params,
            data=None,
            files=None,
        )
        data = response.json()
        return PaginatedList(
            [Question.model_validate(obj=item) for item in data["questions"]],
            total=data["total"],
            next_page=data.get("next_page"),
            prev_page=data.get("prev_page"),
        )

    async def create(
        self,
        *,
        title: str,
        language: Language | str,
        description: str | None = None,
        contents: str | None = None,
        solution: str | None = None,
        ai_assist_custom_system_prompt: str | None = None,
        candidate_instructions: (Sequence[CandidateInstruction] | None) = None,
        file_contents: (Sequence[QuestionFileContent] | None) = None,
        zip_file: Path | None = None,
    ) -> Question:
        """Create a new question.

        Args:
            title: Title for the question.
            language: Programming language for the
                question.
            description: Notes about the question.
            contents: Text inserted into the interview
                session. Cannot be combined with
                ``file_contents``.
            solution: The solution to the question.
            ai_assist_custom_system_prompt: Custom system prompt for AI Assist.
            candidate_instructions: Progressively-revealed
                instruction blocks shown to the candidate.
            file_contents: Files for a multi-file question.
                Cannot be combined with ``contents`` or
                ``zip_file``.
            zip_file: Path to a zip archive containing
                files for a multi-file question. Cannot be
                combined with ``file_contents``.

        Returns:
            The created question.
        """
        validate_mutually_exclusive_question_content(
            contents=contents,
            file_contents=file_contents,
            zip_file=zip_file,
        )
        lang = language
        data: dict[str, str] = {
            "question[title]": title,
            "question[language]": lang,
        }
        if description is not None:
            data["question[description]"] = description
        if contents is not None:
            data["question[contents]"] = contents
        if solution is not None:
            data["question[solution]"] = solution
        if ai_assist_custom_system_prompt is not None:
            data["question[ai_assist_custom_system_prompt]"] = (
                ai_assist_custom_system_prompt
            )
        if candidate_instructions is not None:
            data["question[candidate_instructions]"] = json.dumps(
                obj=[
                    {
                        "instructions": ci.instructions,
                        "default_visible": ci.default_visible,
                    }
                    for ci in candidate_instructions
                ],
            )
        if file_contents is not None:
            data["question[file_contents]"] = json.dumps(
                obj=[
                    {
                        "path": fc.path,
                        "contents": fc.contents,
                    }
                    for fc in file_contents
                ],
            )
        files: dict[str, tuple[str, bytes, str]] | None = None
        if zip_file is not None:
            files = {
                "question[zip_file]": (
                    zip_file.name,
                    zip_file.read_bytes(),  # noqa: ASYNC240
                    "application/zip",
                ),
            }
        response = await self._request(
            method="POST",
            url="/api/questions/",
            data=data,
            files=files,
            params=None,
        )
        return Question.model_validate(obj=response.json())

    async def get(
        self,
        *,
        question_id: str,
    ) -> Question:
        """Retrieve a question by id.

        Args:
            question_id: The id of the question.

        Returns:
            The question.
        """
        response = await self._request(
            method="GET",
            url=f"/api/questions/{question_id}",
            params=None,
            data=None,
            files=None,
        )
        return Question.model_validate(obj=response.json())

    async def update(
        self,
        *,
        question_id: str,
        title: str | None = None,
        language: Language | str | None = None,
        description: str | None = None,
        contents: str | None = None,
        solution: str | None = None,
        ai_assist_custom_system_prompt: str | None = None,
        candidate_instructions: (Sequence[CandidateInstruction] | None) = None,
        file_contents: (Sequence[QuestionFileContent] | None) = None,
        zip_file: Path | None = None,
    ) -> None:
        """Modify an existing question.

        Args:
            question_id: The id of the question.
            title: New title for the question.
            language: New programming language.
            description: New description.
            contents: New contents. Cannot be combined with
                ``file_contents``.
            solution: New solution.
            ai_assist_custom_system_prompt: Custom system prompt for AI Assist.
            candidate_instructions: Progressively-revealed
                instruction blocks shown to the candidate.
            file_contents: Files for a multi-file question.
                Cannot be combined with ``contents`` or
                ``zip_file``.
            zip_file: Path to a zip archive containing
                files for a multi-file question. Cannot be
                combined with ``file_contents``.
        """
        validate_mutually_exclusive_question_content(
            contents=contents,
            file_contents=file_contents,
            zip_file=zip_file,
        )
        data: dict[str, str] = {}
        if title is not None:
            data["question[title]"] = title
        if language is not None:
            lang = language
            data["question[language]"] = lang
        if description is not None:
            data["question[description]"] = description
        if contents is not None:
            data["question[contents]"] = contents
        if solution is not None:
            data["question[solution]"] = solution
        if ai_assist_custom_system_prompt is not None:
            data["question[ai_assist_custom_system_prompt]"] = (
                ai_assist_custom_system_prompt
            )
        if candidate_instructions is not None:
            data["question[candidate_instructions]"] = json.dumps(
                obj=[
                    {
                        "instructions": ci.instructions,
                        "default_visible": ci.default_visible,
                    }
                    for ci in candidate_instructions
                ],
            )
        if file_contents is not None:
            data["question[file_contents]"] = json.dumps(
                obj=[
                    {
                        "path": fc.path,
                        "contents": fc.contents,
                    }
                    for fc in file_contents
                ],
            )
        files: dict[str, tuple[str, bytes, str]] | None = None
        if zip_file is not None:
            files = {
                "question[zip_file]": (
                    zip_file.name,
                    zip_file.read_bytes(),  # noqa: ASYNC240
                    "application/zip",
                ),
            }
        await self._request(
            method="PUT",
            url=f"/api/questions/{question_id}",
            data=data,
            files=files,
            params=None,
        )

    async def delete(
        self,
        *,
        question_id: str,
    ) -> None:
        """Delete a question.

        Args:
            question_id: The id of the question.
        """
        await self._request(
            method="DELETE",
            url=f"/api/questions/{question_id}",
            params=None,
            data=None,
            files=None,
        )


@beartype
class AsyncOrganizationPadsNamespace(_AsyncNamespace):
    """Namespace for async organization pad operations."""

    async def list(
        self,
        *,
        sort: SortOrder | None = None,
        page: int | None = None,
    ) -> PaginatedList[Pad]:
        """Retrieve pads for the entire organization.

        Args:
            sort: Sort order.
            page: Page number for pagination.

        Returns:
            The list of pads with pagination metadata.
        """
        params: dict[str, str | int] = {}
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        response = await self._request(
            method="GET",
            url="/api/organization/pads",
            params=params,
            data=None,
            files=None,
        )
        data = response.json()
        return PaginatedList(
            [Pad.from_dict(data=item) for item in data["pads"]],
            total=data["total"],
            next_page=data.get("next_page"),
            prev_page=data.get("prev_page"),
        )


@beartype
class AsyncOrganizationQuestionsNamespace(
    _AsyncNamespace,
):
    """Namespace for async organization question
    operations.
    """

    async def list(
        self,
        *,
        sort: SortOrder | None = None,
        page: int | None = None,
    ) -> PaginatedList[Question]:
        """Retrieve questions for the entire organization.

        Args:
            sort: Sort order.
            page: Page number for pagination.

        Returns:
            The list of questions with pagination
            metadata.
        """
        params: dict[str, str | int] = {}
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        response = await self._request(
            method="GET",
            url="/api/organization/questions",
            params=params,
            data=None,
            files=None,
        )
        data = response.json()
        return PaginatedList(
            [Question.model_validate(obj=item) for item in data["questions"]],
            total=data["total"],
            next_page=data.get("next_page"),
            prev_page=data.get("prev_page"),
        )


@beartype
class AsyncOrganizationUsersNamespace(_AsyncNamespace):
    """Namespace for async organization user operations."""

    async def list(
        self,
        *,
        email: str | None = None,
    ) -> builtins.list[OrganizationUser]:
        """Retrieve users in the organization.

        Args:
            email: Return only the user with this email address.

        Returns:
            The organization users matching the filter.
        """
        params: dict[str, str | int] = {}
        if email is not None:
            params["email"] = email
        response = await self._request(
            method="GET",
            url="/api/organization/users",
            params=params,
            data=None,
            files=None,
        )
        return [
            OrganizationUser.model_validate(obj=item)
            for item in response.json()["users"]
        ]


@beartype
class AsyncOrganizationNamespace(_AsyncNamespace):
    """Namespace for async organization operations."""

    def __init__(
        self,
        *,
        transport: AsyncTransport,
        base_url: str,
        headers: dict[str, str],
    ) -> None:
        """Create a new async organization namespace.

        Args:
            transport: The async HTTP transport.
            base_url: The base URL for the API.
            headers: Headers to send with every request.
        """
        super().__init__(
            transport=transport,
            base_url=base_url,
            headers=headers,
        )
        self.pads: AsyncOrganizationPadsNamespace = (
            AsyncOrganizationPadsNamespace(
                transport=transport,
                base_url=base_url,
                headers=headers,
            )
        )
        self.questions: AsyncOrganizationQuestionsNamespace = (
            AsyncOrganizationQuestionsNamespace(
                transport=transport,
                base_url=base_url,
                headers=headers,
            )
        )
        self.users: AsyncOrganizationUsersNamespace = (
            AsyncOrganizationUsersNamespace(
                transport=transport,
                base_url=base_url,
                headers=headers,
            )
        )

    async def get(self) -> Organization:
        """Retrieve organization information.

        Returns:
            The organization details.
        """
        response = await self._request(
            method="GET",
            url="/api/organization",
            params=None,
            data=None,
            files=None,
        )
        return Organization.from_dict(
            data=response.json(),
        )

    async def get_stats(
        self,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> OrganizationStats:
        """Retrieve pad usage stats for the organization.

        Args:
            start_time: ISO 8601 start of the search
                window.
            end_time: ISO 8601 end of the search window.

        Returns:
            The usage statistics.
        """
        params: dict[str, str | int] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        response = await self._request(
            method="GET",
            url="/api/organization/stats",
            params=params,
            data=None,
            files=None,
        )
        return OrganizationStats.from_dict(
            data=response.json(),
        )

    async def get_quota(self) -> Quota:
        """Retrieve quota information.

        Returns:
            The quota details.
        """
        response = await self._request(
            method="GET",
            url="/api/quota",
            params=None,
            data=None,
            files=None,
        )
        return Quota.model_validate(obj=response.json())


@beartype
class AsyncCoderPad:
    """An async client for the CoderPad Interview API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = ("https://app.coderpad.io"),
        screen_api_key: str | None = None,
        screen_base_url: str = SCREEN_US_BASE_URL,
        transport: AsyncTransport | None = None,
        screen_transport: AsyncJSONTransport | None = None,
        default_headers: dict[str, str] | None = None,
        limits: httpx.Limits | None = None,
        proxy: str | httpx.Proxy | None = None,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        """Create a new async CoderPad client.

        Args:
            api_key: The API key for authentication.
            base_url: The base URL for the API.
            screen_api_key: The independent Screen API key.
            screen_base_url: The US, EU, or custom Screen base URL.
            transport: The async HTTP transport. Defaults
                to ``AsyncHTTPXTransport()``.
            screen_transport: The independent Screen HTTP transport.
            default_headers: Extra headers merged into every Interview
                and Screen request. Authorization and API-Key values
                from these headers are overwritten by the client keys.
            limits: Optional connection pool limits for default transports.
            proxy: Optional proxy for the default httpx transports.
            timeout: Optional timeout for the default httpx transports.
        """
        self.base_url = base_url
        self._limits = limits
        self._proxy = proxy
        self._timeout = timeout
        resolved_transport = transport or AsyncHTTPXTransport(
            limits=limits,
            proxy=proxy,
            timeout=timeout,
        )
        headers = {
            **(default_headers or {}),
            "Authorization": f'Token token="{api_key}"',
        }
        self.pads: AsyncPadsNamespace = AsyncPadsNamespace(
            transport=resolved_transport,
            base_url=base_url,
            headers=headers,
        )
        self.questions: AsyncQuestionsNamespace = AsyncQuestionsNamespace(
            transport=resolved_transport,
            base_url=base_url,
            headers=headers,
        )
        self._screen_api_key = screen_api_key
        self._screen_base_url = screen_base_url
        self._screen_transport = screen_transport
        self._default_headers = default_headers
        self._screen: AsyncScreenNamespace | None = None

        async def _noop() -> None:
            """No-op close for transports without aclose."""

        if isinstance(
            resolved_transport,
            (AsyncHTTPXTransport, AsyncHTTPX2Transport),
        ):
            self._aclose = resolved_transport.aclose
        else:
            self._aclose = _noop
        if isinstance(
            screen_transport, (AsyncHTTPXTransport, AsyncHTTPX2Transport)
        ):
            self._screen_aclose = screen_transport.aclose
        else:
            self._screen_aclose = _noop
        self.organization: AsyncOrganizationNamespace = (
            AsyncOrganizationNamespace(
                transport=resolved_transport,
                base_url=base_url,
                headers=headers,
            )
        )

    @property
    def screen(self) -> AsyncScreenNamespace:
        """Screen API namespace, created on first access.

        Raises:
            ValueError: If ``screen_api_key`` was not provided.
        """
        if self._screen is None:
            if self._screen_api_key is None:
                msg = "screen_api_key is required to use the Screen API"
                raise ValueError(msg)
            resolved_screen_transport = (
                self._screen_transport
                or AsyncHTTPXTransport(
                    limits=self._limits,
                    proxy=self._proxy,
                    timeout=self._timeout,
                )
            )
            if self._screen_transport is None and isinstance(
                resolved_screen_transport,
                (AsyncHTTPXTransport, AsyncHTTPX2Transport),
            ):
                self._screen_aclose = resolved_screen_transport.aclose
            self._screen_transport = resolved_screen_transport
            self._screen = AsyncScreenNamespace(
                transport=resolved_screen_transport,
                api_key=self._screen_api_key,
                base_url=self._screen_base_url,
                default_headers=self._default_headers,
            )
        return self._screen

    @classmethod
    def from_env(cls) -> Self:
        """Create a client using ``CODERPAD_API_KEY`` and optional Screen
        key.

        Reads ``CODERPAD_API_KEY`` (required) and
        ``CODERPAD_SCREEN_API_KEY`` (optional) from the environment.

        Returns:
            A new async client configured from environment variables.

        Raises:
            KeyError: If ``CODERPAD_API_KEY`` is not set.
        """
        return cls(
            api_key=os.environ["CODERPAD_API_KEY"],
            screen_api_key=os.environ.get(key="CODERPAD_SCREEN_API_KEY"),
        )

    async def aclose(self) -> None:
        """Close the underlying transport."""
        await self._aclose()
        await self._screen_aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            This client instance.
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
