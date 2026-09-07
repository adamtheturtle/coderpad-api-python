"""Types for the CoderPad Interview API."""

import enum
from collections.abc import Iterable
from typing import ClassVar, Self, TypeVar

from beartype import beartype
from pydantic import BaseModel, ConfigDict, Field, field_validator

from coderpad._dict_types import (
    CandidateInstructionDict,
    CustomDatabaseColumnDict,
    CustomDatabaseDict,
    CustomDatabaseSchemaDict,
    CustomDatabaseTableDict,
    CustomFileDict,
    FileContentDict,
    OrganizationDict,
    OrganizationStatsDict,
    OrganizationStatsUserDict,
    OrganizationUserDict,
    PadDict,
    PadEnvironmentDict,
    PadEventDict,
    PadHistoryEntryDict,
    PadInterviewerNotificationDict,
    QuestionDict,
    QuotaDict,
    TeamDict,
    TestCaseDict,
)

_T = TypeVar("_T")


class _APIModel(BaseModel):
    """Base model shared by CoderPad API resources."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
    )


@beartype
class PaginatedList(list[_T]):
    """A list with pagination metadata from the API response."""

    def __init__(
        self,
        iterable: Iterable[_T] = (),
        /,
        *,
        total: int,
        next_page: str | None = None,
        prev_page: str | None = None,
    ) -> None:
        """Create a new paginated list.

        Args:
            iterable: The items for the list.
            total: Total number of items across all pages.
            next_page: URL for the next page, or ``None``.
            prev_page: URL for the previous page, or ``None``.
        """
        super().__init__(iterable)
        self.total = total
        self.next_page = next_page
        self.prev_page = prev_page

    def __repr__(self) -> str:
        """Return a concise debug representation."""
        return (
            f"PaginatedList(len={len(self)}, total={self.total}, "
            f"next_page={self.next_page!r})"
        )


class SortOrder(enum.StrEnum):
    """Sort order for list endpoints."""

    CREATED_AT_ASC = "created_at,asc"
    CREATED_AT_DESC = "created_at,desc"
    UPDATED_AT_ASC = "updated_at,asc"
    UPDATED_AT_DESC = "updated_at,desc"


class Language(enum.StrEnum):
    """Programming language for pads and questions.

    Single-file languages use a simple editor. Multi-file and
    framework languages support ``file_contents`` and
    ``zip_file`` uploads.
    """

    # Single-file languages
    BASH = "bash"
    C = "c"
    CLOJURE = "clojure"
    COFFEESCRIPT = "coffeescript"
    CPP = "cpp"
    CSHARP = "csharp"
    DART = "dart"
    ELIXIR = "elixir"
    ERLANG = "erlang"
    FSHARP = "fsharp"
    GO = "go"
    GSHEETS = "gsheets"
    HACK = "hack"
    HASKELL = "haskell"
    HTML = "html"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    JULIA = "julia"
    KOTLIN = "kotlin"
    LUA = "lua"
    MARKDOWN = "markdown"
    MYSQL = "mysql"
    OBJC = "objc"
    OCAML = "ocaml"
    PERL = "perl"
    PHP = "php"
    PLAINTEXT = "plaintext"
    POSTGRESQL = "postgresql"
    POWERSHELL = "powershell"
    PYTHON = "python"
    PYTHON3 = "python3"
    R = "r"
    RUBY = "ruby"
    RUST = "rust"
    SCALA = "scala"
    SOLIDITY = "solidity"
    SWIFT = "swift"
    TCL = "tcl"
    TYPESCRIPT = "typescript"
    VB = "vb"
    VERILOG = "verilog"

    # Multi-file / framework languages
    ANGULAR = "angular"
    DJANGO = "django"
    GIN = "gin"
    KUBERNETES = "kubernetes"
    MULTIFILE_C = "multifile_c"
    MULTIFILE_CPP = "multifile_cpp"
    MULTIFILE_CSHARP = "multifile_csharp"
    MULTIFILE_GO = "multifile_go"
    MULTIFILE_JAVA = "multifile_java"
    MULTIFILE_KOTLIN = "multifile_kotlin"
    MULTIFILE_PHP = "multifile_php"
    MULTIFILE_PYTHON = "multifile_python"
    MULTIFILE_RUBY = "multifile_ruby"
    MULTIFILE_RUST = "multifile_rust"
    MULTIFILE_SCALA = "multifile_scala"
    MULTIFILE_SWIFT = "multifile_swift"
    MULTIFILE_TERRAFORM = "multifile_terraform"
    MULTIFILE_TYPESCRIPT = "multifile_typescript"
    NEXTJS = "nextjs"
    NODEJS = "nodejs"
    RAILS = "rails"
    REACT = "react"
    REACT_NATIVE_WEB = "react-native-web"
    SPRING = "spring"
    SVELTE = "svelte"
    UNIVERSAL = "universal"
    VUE = "vue"


@beartype
class Team(_APIModel):
    """A team within an organization."""

    id: str
    name: str

    @classmethod
    def from_dict(cls, data: TeamDict) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
        )


@beartype
class PadInterviewerNotification(_APIModel):
    """An interviewer notification associated with a pad.

    This structure is empirically observed in live API responses and is not
    currently described by the published CoderPad API specification.
    """

    id: int
    title: str
    message: str
    priority: str
    request_id: str
    auto_dismissed: bool
    dismissed_at: str | None = None
    useful: bool | None = None
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(
        cls,
        data: PadInterviewerNotificationDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            title=data["title"],
            message=data["message"],
            priority=data["priority"],
            request_id=data["request_id"],
            auto_dismissed=data["auto_dismissed"],
            dismissed_at=data.get("dismissed_at"),
            useful=data.get("useful"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


def _empty_pad_interviewer_notifications() -> list[PadInterviewerNotification]:
    """Return an empty, precisely typed notification list."""
    return []


@beartype
class Pad(_APIModel):
    """A CoderPad interview pad.

    Not every field here can be written via ``create`` or ``update``.
    See the "Writable and read-only fields" reference for the matrix.
    """

    id: str
    title: str
    state: str
    owner_email: str
    language: str | None = None
    private: bool
    execution_enabled: bool
    contents: str | None = None
    participants: list[str]
    events: str
    notes: str | None = None
    created_at: str
    updated_at: str
    ended_at: str | None = None
    url: str
    playback: str
    drawing: str | None = None
    type: str
    question_ids: list[int]
    pad_environment_ids: list[int]
    active_environment_id: int | None = None
    team: Team
    history: str | None = None
    restrict_interviewer_access: bool | None = None
    pad_interviewer_notifications: list[PadInterviewerNotification] = Field(
        default_factory=_empty_pad_interviewer_notifications,
    )

    @classmethod
    def from_dict(cls, data: PadDict) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        raw_notifications = data.get("pad_interviewer_notifications")
        notifications = (
            [
                PadInterviewerNotification.from_dict(data=item)
                for item in raw_notifications
            ]
            if raw_notifications is not None
            else _empty_pad_interviewer_notifications()
        )
        return cls(
            id=data["id"],
            title=data["title"],
            state=data["state"],
            owner_email=data["owner_email"],
            language=data.get("language"),
            private=data["private"],
            execution_enabled=data["execution_enabled"],
            contents=data.get("contents"),
            participants=data["participants"],
            events=data["events"],
            notes=data.get("notes"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            ended_at=data.get("ended_at"),
            url=data["url"],
            playback=data["playback"],
            drawing=data.get("drawing"),
            type=data["type"],
            question_ids=data["question_ids"],
            pad_environment_ids=data["pad_environment_ids"],
            active_environment_id=data.get(
                "active_environment_id",
            ),
            team=Team.from_dict(data=data["team"]),
            history=data.get("history"),
            restrict_interviewer_access=data.get(
                "restrict_interviewer_access",
            ),
            pad_interviewer_notifications=notifications,
        )


@beartype
class PadEvent(_APIModel):
    """An event associated with a pad."""

    message: str
    kind: str
    metadata: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    created_at: str

    @classmethod
    def from_dict(
        cls,
        data: PadEventDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            message=data["message"],
            kind=data["kind"],
            metadata=data.get("metadata"),
            user_name=data.get("user_name"),
            user_email=data.get("user_email"),
            created_at=data["created_at"],
        )


@beartype
class PadHistoryEntry(_APIModel):
    """An editor operation from a pad's Firebase history.

    Positive integer operations retain existing characters, negative
    integers delete characters, and strings insert text.
    """

    id: str
    author: str
    operations: list[int | str]
    timestamp: int

    @classmethod
    def from_dict(
        cls,
        *,
        entry_id: str,
        data: PadHistoryEntryDict,
    ) -> Self:
        """Create from a Firebase history entry.

        Args:
            entry_id: The Firebase key for the entry.
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=entry_id,
            author=data["a"],
            operations=data["o"],
            timestamp=data["t"],
        )

    def apply(self, *, contents: str) -> str:
        """Apply this operation to existing file contents.

        Args:
            contents: The contents immediately before this operation.

        Returns:
            The updated contents.
        """
        cursor = 0
        updated: list[str] = []
        for operation in self.operations:
            if isinstance(operation, str):
                updated.append(operation)
            elif operation > 0:
                updated.append(contents[cursor : cursor + operation])
                cursor += operation
            else:
                cursor -= operation
        updated.append(contents[cursor:])
        return "".join(updated)


def _history_sort_key(
    item: tuple[str, PadHistoryEntryDict],
    /,
) -> tuple[int, str]:
    """Return the sort key for a Firebase history entry: timestamp, then ID."""
    entry_id, entry = item
    return (entry["t"], entry_id)


@beartype
class PadHistory(list[PadHistoryEntry]):
    """Chronologically ordered editor history for a pad file."""

    @classmethod
    def from_dict(
        cls,
        *,
        data: dict[str, PadHistoryEntryDict],
    ) -> Self:
        """Create from a Firebase history response.

        Args:
            data: Firebase keys mapped to editor operations.

        Returns:
            A chronologically ordered history.
        """
        ordered_entries = sorted(
            data.items(),
            key=_history_sort_key,
        )
        history = cls()
        for entry_id, entry in ordered_entries:
            history.append(
                PadHistoryEntry.from_dict(
                    entry_id=entry_id,
                    data=entry,
                ),
            )
        return history

    def replay(self, *, initial_contents: str = "") -> str:
        """Replay all operations and return the resulting contents.

        Args:
            initial_contents: Contents before the first operation.

        Returns:
            The contents after all operations.
        """
        contents = initial_contents
        for entry in self:
            contents = entry.apply(contents=contents)
        return contents


@beartype
class FileContent(_APIModel):
    """A file within a pad environment.

    Binary files are empirically observed with ``binary`` set to ``True`` and
    ``contents`` set to ``None``; these fields are not fully described by the
    published API specification.
    """

    path: str
    contents: str | None
    history: str | None = None
    binary: bool = False

    @classmethod
    def from_dict(
        cls,
        data: FileContentDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        raw_binary = data.get("binary")
        return cls(
            path=data["path"],
            contents=data["contents"],
            history=data.get("history"),
            binary=raw_binary if raw_binary is not None else False,
        )


@beartype
class PadEnvironment(_APIModel):
    """A pad environment."""

    id: int
    pad_id: int
    question_id: int | None = None
    example_question_id: int | None = None
    language: str
    file_contents: list[FileContent]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(
        cls,
        data: PadEnvironmentDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            pad_id=data["pad_id"],
            question_id=data.get("question_id"),
            example_question_id=data.get(
                "example_question_id",
            ),
            language=data["language"],
            file_contents=[
                FileContent.from_dict(data=item)
                for item in data["file_contents"]
            ],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@beartype
class QuestionFileContent(_APIModel):
    """A file for a multi-file question.

    Used when creating or updating questions with
    multi-file languages.
    """

    path: str
    contents: str


@beartype
class CandidateInstruction(_APIModel):
    """Instructions shown to a candidate."""

    instructions: str
    default_visible: bool = False

    @field_validator("default_visible", mode="before")
    @classmethod
    def _none_is_not_visible(cls, value: object) -> object:
        """Normalize a null API value to the legacy false default."""
        return False if value is None else value

    @classmethod
    def from_dict(
        cls,
        data: CandidateInstructionDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            instructions=data["instructions"],
            default_visible=(
                "default_visible" in data and data["default_visible"]
            ),
        )


@beartype
class TestCase(_APIModel):
    """A test case for a question."""

    id: int
    return_value: str
    visible: bool
    arguments: list[str]

    @classmethod
    def from_dict(
        cls,
        data: TestCaseDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            return_value=data["return_value"],
            visible=data["visible"],
            arguments=data["arguments"],
        )


@beartype
class CustomFile(_APIModel):
    """A custom file attached to a question."""

    id: str
    title: str
    description: str
    filename: str
    filesize: str

    @classmethod
    def from_dict(
        cls,
        data: CustomFileDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            filename=data["filename"],
            filesize=data["filesize"],
        )


@beartype
class CustomDatabaseColumn(_APIModel):
    """A column in a question's custom database schema."""

    name: str
    type: str
    pk: bool
    nn: bool

    @classmethod
    def from_dict(
        cls,
        data: CustomDatabaseColumnDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            name=data["name"],
            type=data["type"],
            pk=data["pk"],
            nn=data["nn"],
        )


@beartype
class CustomDatabaseTable(_APIModel):
    """A table in a question's custom database schema."""

    name: str
    columns: list[CustomDatabaseColumn]

    @classmethod
    def from_dict(
        cls,
        data: CustomDatabaseTableDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            name=data["name"],
            columns=[
                CustomDatabaseColumn.from_dict(data=item)
                for item in data["columns"]
            ],
        )


@beartype
class CustomDatabaseSchema(_APIModel):
    """The structured schema for a question's custom database."""

    arrangement: str
    tables: list[CustomDatabaseTable]

    @classmethod
    def from_dict(
        cls,
        data: CustomDatabaseSchemaDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            arrangement=data["arrangement"],
            tables=[
                CustomDatabaseTable.from_dict(data=item)
                for item in data["tables"]
            ],
        )


@beartype
class CustomDatabase(_APIModel):
    """A custom database attached to a question.

    This structure is empirically observed in live API responses and is not
    currently described by the published CoderPad API specification.
    """

    id: int
    title: str
    description: str
    language: str
    # These API field names intentionally shadow deprecated BaseModel methods.
    # Pydantic supports this at runtime (pydantic/pydantic#11912), but static
    # type checkers still treat the fields as incompatible method overrides.
    schema: str  # type: ignore[assignment]  # pyright: ignore[reportIncompatibleMethodOverride]
    schema_json: CustomDatabaseSchema  # type: ignore[assignment]  # pyright: ignore[reportIncompatibleMethodOverride]

    @classmethod
    def from_dict(
        cls,
        data: CustomDatabaseDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            language=data["language"],
            schema=data["schema"],
            schema_json=CustomDatabaseSchema.from_dict(
                data=data["schema_json"],
            ),
        )


@beartype
class Question(_APIModel):
    """A CoderPad question.

    Not every field here can be written via ``create`` or ``update``.
    See the "Writable and read-only fields" reference for the matrix.
    """

    id: int
    title: str
    owner_email: str
    language: str | None = None
    description: str | None = None
    candidate_instructions: list[CandidateInstruction]
    contents: str | None = None
    shared: bool
    used: int
    take_home: bool
    test_cases_enabled: bool
    solution: str | None = None
    pad_type: str
    is_draft: bool
    author_name: str
    organization_name: str
    custom_files: list[CustomFile]
    created_at: str
    updated_at: str
    public_take_home_setting_id: int | None = None
    contents_for_test_cases: str | None = None
    test_cases: list[TestCase] | None = None
    custom_database: CustomDatabase | None = None
    ai_assist_custom_system_prompt: str | None = None

    @classmethod
    def from_dict(
        cls,
        data: QuestionDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        raw_test_cases = data.get("test_cases")
        raw_custom_database = data.get("custom_database")
        return cls(
            id=data["id"],
            title=data["title"],
            owner_email=data["owner_email"],
            language=data.get("language"),
            description=data.get("description"),
            candidate_instructions=[
                CandidateInstruction.from_dict(data=item)
                for item in data["candidate_instructions"]
            ],
            contents=data.get("contents"),
            shared=data["shared"],
            used=data["used"],
            take_home=data["take_home"],
            test_cases_enabled=data["test_cases_enabled"],
            solution=data.get("solution"),
            pad_type=data["pad_type"],
            is_draft=data["is_draft"],
            author_name=data["author_name"],
            organization_name=data["organization_name"],
            custom_files=[
                CustomFile.from_dict(data=item)
                for item in data["custom_files"]
            ],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            public_take_home_setting_id=data.get(
                "public_take_home_setting_id",
            ),
            contents_for_test_cases=data.get(
                "contents_for_test_cases",
            ),
            test_cases=[
                TestCase.from_dict(data=item) for item in raw_test_cases
            ]
            if raw_test_cases is not None
            else None,
            custom_database=CustomDatabase.from_dict(
                data=raw_custom_database,
            )
            if raw_custom_database is not None
            else None,
            ai_assist_custom_system_prompt=data.get(
                "ai_assist_custom_system_prompt",
            ),
        )


@beartype
class OrganizationUser(_APIModel):
    """A user within an organization."""

    email: str
    name: str
    teams: list[str]

    @classmethod
    def from_dict(
        cls,
        data: OrganizationUserDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            email=data["email"],
            name=data["name"],
            teams=data["teams"],
        )


@beartype
class OrganizationStatsUser(_APIModel):
    """A user's pad usage statistics."""

    email: str
    name: str
    pads_created: int

    @classmethod
    def from_dict(
        cls,
        data: OrganizationStatsUserDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            email=data["email"],
            name=data["name"],
            pads_created=data["pads_created"],
        )


@beartype
class Quota(_APIModel):
    """Quota information."""

    trial_expires_at: str
    pads_used: int
    quota_reset_at: str
    unlimited: bool
    overages_enabled: bool

    @classmethod
    def from_dict(
        cls,
        data: QuotaDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            trial_expires_at=data["trial_expires_at"],
            pads_used=data["pads_used"],
            quota_reset_at=data["quota_reset_at"],
            unlimited=data["unlimited"],
            overages_enabled=data["overages_enabled"],
        )


def _empty_child_organizations() -> list[dict[str, object]]:
    """Return an empty list for a response structure not yet typed."""
    return []


@beartype
class Organization(_APIModel):
    """Organization information.

    ``id`` and ``child_organizations`` are empirically observed fields that
    are not currently described by the published API specification. Child
    organizations remain raw mappings until their non-empty shape is known.
    """

    organization_name: str
    user_count: int
    users: list[OrganizationUser]
    organization_default_language: str
    single_sign_on_supported: bool
    teams: list[Team]
    single_sign_in_url: str | None = None
    id: int | None = None
    child_organizations: list[dict[str, object]] = Field(
        default_factory=_empty_child_organizations,
    )

    @classmethod
    def from_dict(
        cls,
        data: OrganizationDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        raw_child_organizations = data.get("child_organizations")
        return cls(
            organization_name=data["organization_name"],
            user_count=data["user_count"],
            users=[
                OrganizationUser.from_dict(data=item) for item in data["users"]
            ],
            organization_default_language=data[
                "organization_default_language"
            ],
            single_sign_on_supported=data["single_sign_on_supported"],
            teams=[Team.from_dict(data=item) for item in data["teams"]],
            single_sign_in_url=data.get("single_sign_in_url"),
            id=data.get("id"),
            child_organizations=(
                raw_child_organizations
                if raw_child_organizations is not None
                else _empty_child_organizations()
            ),
        )


@beartype
class OrganizationStats(_APIModel):
    """Organization usage statistics."""

    start_time: str
    end_time: str
    pads_created: int
    users: list[OrganizationStatsUser]

    @classmethod
    def from_dict(
        cls,
        data: OrganizationStatsDict,
    ) -> Self:
        """Create from an API response dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A new instance.
        """
        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            pads_created=data["pads_created"],
            users=[
                OrganizationStatsUser.from_dict(data=item)
                for item in data["users"]
            ],
        )
