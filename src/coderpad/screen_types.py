"""Types for the CoderPad Screen API."""

from typing import ClassVar, Self, TypeGuard, override

from beartype import beartype
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _APIModel(BaseModel):
    """Base model shared by CoderPad Screen API resources."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
    )


def _is_object_list(value: object, /) -> TypeGuard[list[object]]:
    """Return whether an API value is a list."""
    return isinstance(value, list)


def _is_object_mapping(
    value: object,
    /,
) -> TypeGuard[dict[object, object]]:
    """Return whether an API value is a mapping."""
    return isinstance(value, dict)


def _objects(value: object, /) -> list[object]:
    """Return an object list from an API value."""
    return value if _is_object_list(value) else []


def _mapping(value: object, /) -> dict[str, object] | None:
    """Return a string-keyed mapping from an API value."""
    if not _is_object_mapping(value):
        return None
    return {key: item for key, item in value.items() if isinstance(key, str)}


def _strings(value: object, /) -> list[str]:
    """Return a string list from an API value."""
    return [item for item in _objects(value) if isinstance(item, str)]


def _empty_strings() -> list[str]:
    """Create an empty string list."""
    return []


def _optional_int(value: object, /) -> int | None:
    """Return an integer API value when present."""
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool)
        else None
    )


def _required_int(value: object, /) -> int:
    """Return a required integer API value."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    msg = "Expected an integer API value"
    raise TypeError(msg)


def _optional_float(value: object, /) -> float | None:
    """Return a numeric API value when present."""
    return (
        float(value)
        if isinstance(value, int | float) and not isinstance(value, bool)
        else None
    )


def _optional_str(value: object, /) -> str | None:
    """Return a string API value when present."""
    return value if isinstance(value, str) else None


@beartype
class ScreenCampaign(_APIModel):
    """A reusable Screen assessment campaign."""

    id: int
    name: str
    languages: list[str] = Field(default_factory=_empty_strings)
    pinned: bool = False
    archived: bool = False

    @classmethod
    def list_from_value(cls, value: object) -> list[Self]:
        """Create campaigns from an API response value."""
        return [
            cls.from_dict(data=mapping)
            for item in _objects(value)
            if (mapping := _mapping(item)) is not None
        ]

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a campaign from an API response."""
        return cls(
            id=_required_int(data["id"]),
            name=f"{data['name']}",
            languages=_strings(data.get("languages")),
            pinned=data.get("pinned") is True,
            archived=data.get("archived") is True,
        )


@beartype
class ScreenInvitation(_APIModel):
    """An invitation to a Screen campaign.

    ``candidate_email`` and ``candidate_name`` are required by the Screen
    send-invitation API surface (the user interface collects email plus name).
    """

    candidate_email: str | None = None
    candidate_name: str | None = None
    recruiter_email: str | None = None
    tags: str | None = None
    send_invitation_email: bool | None = None
    send_notification_email_on_bounce: bool | None = None

    @model_validator(mode="after")
    def require_email_and_name(self) -> Self:
        """Require candidate email and name before sending."""
        if not self.candidate_email:
            msg = "candidate_email is required"
            raise ValueError(msg)
        if not self.candidate_name:
            msg = "candidate_name is required"
            raise ValueError(msg)
        return self


@beartype
class ScreenInvitationResult(_APIModel):
    """The result of creating a Screen test invitation."""

    id: int | None
    test_url: str | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create an invitation result from an API response."""
        return cls(
            id=_optional_int(data.get("id")),
            test_url=_optional_str(data.get("test_url")),
        )


@beartype
class ScreenTestQuestion(_APIModel):
    """A question included in a Screen test."""

    id: int
    last_activity_time: int | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a question from an API response."""
        return cls(
            id=_required_int(data["id"]),
            last_activity_time=_optional_int(data.get("last_activity_time")),
        )


@beartype
class ScreenSkillResult(_APIModel):
    """A scored skill within a Screen report."""

    points: int | None
    score: float | None
    total_points: int | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a skill result from an API response."""
        return cls(
            points=_optional_int(data.get("points")),
            score=_optional_float(data.get("score")),
            total_points=_optional_int(data.get("total_points")),
        )


@beartype
class ScreenTechnologyResult(_APIModel):
    """A scored technology within a Screen report."""

    points: int | None
    score: float | None
    skills: dict[str, ScreenSkillResult]
    total_points: int | None
    comparative_score: float | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a technology result from an API response."""
        typed_skills = _mapping(data.get("skills"))
        skills = (
            {
                name: ScreenSkillResult.from_dict(data=mapped)
                for name, raw_value in typed_skills.items()
                if (mapped := _mapping(raw_value)) is not None
            }
            if typed_skills is not None
            else {}
        )
        return cls(
            points=_optional_int(data.get("points")),
            score=_optional_float(data.get("score")),
            skills=skills,
            total_points=_optional_int(data.get("total_points")),
            comparative_score=_optional_float(data.get("comparative_score")),
        )


@beartype
class ScreenReport(_APIModel):
    """A candidate's scored Screen report."""

    duration: int | None
    warnings: list[str]
    points: int | None
    score: float | None
    technologies: dict[str, ScreenTechnologyResult]
    total_duration: int | None
    total_points: int | None
    comparative_score: float | None
    community_stats: list[int] | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a report from an API response."""
        typed_technologies = _mapping(data.get("technologies"))
        technologies = (
            {
                name: ScreenTechnologyResult.from_dict(data=mapped)
                for name, raw_value in typed_technologies.items()
                if (mapped := _mapping(raw_value)) is not None
            }
            if typed_technologies is not None
            else {}
        )
        raw_community_stats: object = data.get("community_stats")
        community_items = _objects(raw_community_stats)
        community_stats = (
            [
                item
                for item in community_items
                if isinstance(item, int) and not isinstance(item, bool)
            ]
            if isinstance(raw_community_stats, list)
            else None
        )
        return cls(
            duration=_optional_int(data.get("duration")),
            warnings=_strings(data.get("warnings")),
            points=_optional_int(data.get("points")),
            score=_optional_float(data.get("score")),
            technologies=technologies,
            total_duration=_optional_int(data.get("total_duration")),
            total_points=_optional_int(data.get("total_points")),
            comparative_score=_optional_float(data.get("comparative_score")),
            community_stats=community_stats,
        )


@beartype
class ScreenTest(_APIModel):
    """A candidate's Screen test session."""

    id: int
    status: str
    campaign_id: int | None
    candidate_name: str | None
    candidate_email: str | None
    tags: list[str]
    send_time: int | None
    start_time: int | None
    end_time: int | None
    last_activity_time: int | None
    url: str | None
    test_url: str | None
    report: ScreenReport | None
    questions: list[ScreenTestQuestion]

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a test session from an API response."""
        raw_report = _mapping(data.get("report"))
        typed_questions = _objects(data.get("questions"))
        return cls(
            id=_required_int(data["id"]),
            status=_optional_str(data.get("status")) or "unknown",
            campaign_id=_optional_int(data.get("campaign_id")),
            candidate_name=_optional_str(data.get("candidate_name")),
            candidate_email=_optional_str(data.get("candidate_email")),
            tags=_strings(data.get("tags")),
            send_time=_optional_int(data.get("send_time")),
            start_time=_optional_int(data.get("start_time")),
            end_time=_optional_int(data.get("end_time")),
            last_activity_time=_optional_int(data.get("last_activity_time")),
            url=_optional_str(data.get("url")),
            test_url=_optional_str(data.get("test_url")),
            report=ScreenReport.from_dict(data=raw_report)
            if raw_report is not None
            else None,
            questions=[
                ScreenTestQuestion.from_dict(data=mapping)
                for item in typed_questions
                if (mapping := _mapping(item)) is not None
            ],
        )


@beartype
class ScreenPagination(_APIModel):
    """Offset pagination metadata returned by Screen."""

    start: int | None
    limit: int | None
    total: int | None
    has_more_items: bool
    next_start: int | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create pagination metadata from an API response."""
        return cls(
            start=_optional_int(data.get("start")),
            limit=_optional_int(data.get("limit")),
            total=_optional_int(data.get("total")),
            has_more_items=data.get("has_more_items") is True,
            next_start=_optional_int(data.get("next_start")),
        )


@beartype
class ScreenTestsPage(_APIModel):
    """One page of Screen test sessions."""

    tests: list[ScreenTest]
    pagination: ScreenPagination | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a tests page from an API response."""
        typed_tests = _objects(data.get("tests"))
        raw_pagination = _mapping(data.get("pagination"))
        return cls(
            tests=[
                ScreenTest.from_dict(data=mapping)
                for item in typed_tests
                if (mapping := _mapping(item)) is not None
            ],
            pagination=ScreenPagination.from_dict(data=raw_pagination)
            if raw_pagination is not None
            else None,
        )

    @override
    def __repr__(self) -> str:
        """Return a concise debug representation."""
        return (
            f"ScreenTestsPage(tests={len(self.tests)}, "
            f"pagination={self.pagination!r})"
        )


@beartype
class ScreenWebhook(_APIModel):
    """The configured Screen webhook."""

    url: str | None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create webhook configuration from an API response."""
        return cls(url=_optional_str(data.get("url")))
