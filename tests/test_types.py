"""Tests for the CoderPad types."""

import pytest
from pydantic import ValidationError

from coderpad._dict_types import (
    CandidateInstructionDict,
    CustomDatabaseDict,
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
from coderpad.screen_types import ScreenPagination, ScreenTestsPage
from coderpad.types import (
    CandidateInstruction,
    CustomDatabase,
    CustomFile,
    FileContent,
    Organization,
    OrganizationStats,
    OrganizationStatsUser,
    OrganizationUser,
    Pad,
    PadEnvironment,
    PadEvent,
    PadHistory,
    PadHistoryEntry,
    PadInterviewerNotification,
    PaginatedList,
    Question,
    Quota,
    Team,
    TestCase,
)


def _team_dict() -> TeamDict:
    """Sample TeamDict."""
    return {"id": "team-1", "name": "Backend"}


def _pad_event_dict() -> PadEventDict:
    """Sample PadEventDict."""
    return {
        "message": "Pad started",
        "kind": "start",
        "metadata": None,
        "user_name": "Alice",
        "user_email": "alice@example.com",
        "created_at": "2023-01-01T00:00:00Z",
    }


def _pad_interviewer_notification_dict() -> PadInterviewerNotificationDict:
    """Sample PadInterviewerNotificationDict."""
    return {
        "id": 11,
        "title": "Interview signal",
        "message": "Consider asking a follow-up question.",
        "priority": "normal",
        "request_id": "request-1",
        "auto_dismissed": False,
        "dismissed_at": None,
        "useful": None,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }


def _file_content_dict() -> FileContentDict:
    """Sample FileContentDict."""
    return {
        "path": "main.py",
        "contents": "print(1)",
        "history": "v1",
        "binary": False,
    }


def _pad_history_entry_dict() -> PadHistoryEntryDict:
    """Sample PadHistoryEntryDict."""
    return {
        "a": "author-1",
        "o": [1, "X", -2],
        "t": 1_700_000_000_000,
    }


def _pad_environment_dict() -> PadEnvironmentDict:
    """Sample PadEnvironmentDict."""
    return {
        "id": 1,
        "pad_id": 2,
        "question_id": 3,
        "example_question_id": 4,
        "language": "python",
        "file_contents": [_file_content_dict()],
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
    }


def _candidate_instruction_dict() -> CandidateInstructionDict:
    """Sample CandidateInstructionDict."""
    return {"instructions": "Do the thing", "default_visible": True}


def _test_case_dict() -> TestCaseDict:
    """Sample TestCaseDict."""
    return {
        "id": 10,
        "return_value": "42",
        "visible": True,
        "arguments": ["1", "2"],
    }


def _custom_file_dict() -> CustomFileDict:
    """Sample CustomFileDict."""
    return {
        "id": "cf-1",
        "title": "Data",
        "description": "Test data",
        "filename": "data.csv",
        "filesize": "1024",
    }


def _custom_database_dict() -> CustomDatabaseDict:
    """Sample CustomDatabaseDict."""
    return {
        "id": 12,
        "title": "Products",
        "description": "Product catalog",
        "language": "postgresql",
        "schema": "CREATE TABLE products (id integer);",
        "schema_json": {
            "arrangement": "horizontal",
            "tables": [
                {
                    "name": "products",
                    "columns": [
                        {
                            "name": "id",
                            "type": "integer",
                            "pk": True,
                            "nn": True,
                        },
                    ],
                },
            ],
        },
    }


def _pad_dict() -> PadDict:
    """Sample PadDict."""
    return {
        "id": "pad-1",
        "title": "Interview",
        "state": "active",
        "owner_email": "owner@example.com",
        "language": "python",
        "private": True,
        "execution_enabled": True,
        "contents": "# code",
        "participants": ["a@example.com"],
        "events": "[]",
        "notes": "Good",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "ended_at": "2023-01-03T00:00:00Z",
        "url": "https://app.coderpad.io/pad-1",
        "playback": "https://app.coderpad.io/pad-1/playback",
        "history": "v1",
        "drawing": "svg-data",
        "type": "sandbox",
        "question_ids": [1, 2],
        "pad_environment_ids": [10],
        "active_environment_id": 10,
        "team": _team_dict(),
        "restrict_interviewer_access": True,
        "pad_interviewer_notifications": [
            _pad_interviewer_notification_dict(),
        ],
    }


_PUBLIC_TAKE_HOME_SETTING_ID = 7


def _question_dict() -> QuestionDict:
    """Sample QuestionDict."""
    return {
        "id": 5,
        "title": "FizzBuzz",
        "owner_email": "owner@example.com",
        "language": "python",
        "description": "Write FizzBuzz",
        "candidate_instructions": [_candidate_instruction_dict()],
        "contents": "def fizzbuzz(): ...",
        "shared": False,
        "used": 3,
        "take_home": False,
        "test_cases_enabled": True,
        "solution": "def fizzbuzz(): pass",
        "pad_type": "standard",
        "is_draft": False,
        "author_name": "Author",
        "organization_name": "Org",
        "custom_files": [_custom_file_dict()],
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "public_take_home_setting_id": _PUBLIC_TAKE_HOME_SETTING_ID,
        "contents_for_test_cases": "test code",
        "test_cases": [_test_case_dict()],
        "custom_database": _custom_database_dict(),
        "ai_assist_custom_system_prompt": "Only provide hints.",
    }


class TestTeam:
    """Tests for ``Team``."""

    @staticmethod
    def test_from_dict() -> None:
        """A Team can be created from a dictionary."""
        data = _team_dict()
        result = Team.from_dict(data=data)
        assert result.id == data["id"]
        assert result.name == data["name"]

    @staticmethod
    def test_pydantic_validation_and_serialization() -> None:
        """Models validate strictly, ignore new API fields, and
        serialize.
        """
        team = Team.model_validate(
            obj={"id": "team-1", "name": "Backend", "future_field": True},
        )
        assert team.model_dump() == {"id": "team-1", "name": "Backend"}
        with pytest.raises(expected_exception=ValidationError):
            _ = Team.model_validate(obj={"id": 1, "name": "Backend"})
        with (
            pytest.MonkeyPatch.context() as monkeypatch,
            pytest.raises(expected_exception=ValidationError),
        ):
            monkeypatch.setattr(
                target=team,
                name="name",
                value="Frontend",
            )


class TestPad:
    """Tests for ``Pad``."""

    @staticmethod
    def test_from_dict() -> None:
        """A Pad can be created from a dictionary."""
        data = _pad_dict()
        result = Pad.from_dict(data=data)
        assert result.id == data["id"]
        assert result.title == data["title"]
        assert result.state == data["state"]
        assert result.owner_email == data["owner_email"]
        assert result.language == data["language"]
        assert result.private == data["private"]
        assert result.execution_enabled == data["execution_enabled"]
        assert result.contents == data["contents"]
        assert result.participants == data["participants"]
        assert result.events == data["events"]
        assert result.notes == data["notes"]
        assert result.created_at == data["created_at"]
        assert result.updated_at == data["updated_at"]
        assert result.ended_at == data["ended_at"]
        assert result.url == data["url"]
        assert result.playback == data["playback"]
        assert result.history == "v1"
        assert result.drawing == data["drawing"]
        assert result.type == data["type"]
        assert result.question_ids == data["question_ids"]
        assert result.pad_environment_ids == data["pad_environment_ids"]
        assert result.active_environment_id == data["active_environment_id"]
        assert result.team.id == data["team"]["id"]
        assert result.restrict_interviewer_access is True
        assert len(result.pad_interviewer_notifications) == 1

    @staticmethod
    def test_from_dict_without_empirically_observed_fields() -> None:
        """A Pad remains compatible with published response fields."""
        data = _pad_dict()
        del data["restrict_interviewer_access"]
        del data["pad_interviewer_notifications"]
        result = Pad.from_dict(data=data)
        assert result.restrict_interviewer_access is None
        assert not bool(result.pad_interviewer_notifications)


class TestPadInterviewerNotification:
    """Tests for ``PadInterviewerNotification``."""

    @staticmethod
    def test_from_dict() -> None:
        """An interviewer notification can be created from a
        dictionary.
        """
        data = _pad_interviewer_notification_dict()
        result = PadInterviewerNotification.from_dict(data=data)
        assert result.id == data["id"]
        assert result.title == data["title"]
        assert result.priority == data["priority"]
        assert result.request_id == data["request_id"]
        assert result.auto_dismissed == data["auto_dismissed"]
        assert result.dismissed_at is None
        assert result.useful is None


class TestPadEvent:
    """Tests for ``PadEvent``."""

    @staticmethod
    def test_from_dict() -> None:
        """A PadEvent can be created from a dictionary."""
        data = _pad_event_dict()
        result = PadEvent.from_dict(data=data)
        assert result.message == data["message"]
        assert result.kind == data["kind"]
        assert result.metadata == data["metadata"]
        assert result.user_name == data["user_name"]
        assert result.user_email == data["user_email"]
        assert result.created_at == data["created_at"]

    @staticmethod
    def test_model_validate_without_optional_fields() -> None:
        """Pydantic parsing accepts omitted optional response fields."""
        result = PadEvent.model_validate(
            obj={
                "message": "Pad started",
                "kind": "start",
                "created_at": "2023-01-01T00:00:00Z",
            },
        )
        assert result.metadata is None
        assert result.user_name is None
        assert result.user_email is None


class TestFileContent:
    """Tests for ``FileContent``."""

    @staticmethod
    def test_from_dict() -> None:
        """A FileContent can be created from a dictionary."""
        data = _file_content_dict()
        result = FileContent.from_dict(data=data)
        assert result.path == data["path"]
        assert result.contents == data["contents"]
        assert result.history == "v1"
        assert result.binary is False

    @staticmethod
    def test_from_dict_without_history() -> None:
        """A FileContent can omit its optional history URL."""
        data: FileContentDict = {
            "path": "main.py",
            "contents": "print(1)",
        }
        result = FileContent.from_dict(data=data)
        assert result.history is None
        assert result.binary is False

    @staticmethod
    def test_from_dict_for_binary_file() -> None:
        """A binary FileContent can have no text contents."""
        data: FileContentDict = {
            "path": "image.png",
            "contents": None,
            "binary": True,
        }
        result = FileContent.from_dict(data=data)
        assert result.contents is None
        assert result.binary is True


class TestPadHistoryEntry:
    """Tests for ``PadHistoryEntry``."""

    @staticmethod
    def test_from_dict() -> None:
        """A history entry can be created from a dictionary."""
        data = _pad_history_entry_dict()
        result = PadHistoryEntry.from_dict(
            entry_id="entry-1",
            data=data,
        )
        assert result.id == "entry-1"
        assert result.author == data["a"]
        assert result.operations == data["o"]
        assert result.timestamp == data["t"]

    @staticmethod
    def test_apply() -> None:
        """Text operations can be applied to existing contents."""
        entry = PadHistoryEntry.from_dict(
            entry_id="entry-1",
            data=_pad_history_entry_dict(),
        )
        assert entry.apply(contents="abcd") == "aXd"


class TestPadHistory:
    """Tests for ``PadHistory``."""

    @staticmethod
    def test_from_dict_orders_and_replays_entries() -> None:
        """History entries are ordered and can be replayed."""
        history = PadHistory.from_dict(
            data={
                "later": {
                    "a": "author-1",
                    "o": [2, "!"],
                    "t": 2,
                },
                "earlier": {
                    "a": "author-1",
                    "o": [1, "i"],
                    "t": 1,
                },
            },
        )
        assert [entry.id for entry in history] == ["earlier", "later"]
        assert history.replay(initial_contents="h") == "hi!"


class TestPadEnvironment:
    """Tests for ``PadEnvironment``."""

    @staticmethod
    def test_from_dict() -> None:
        """A PadEnvironment can be created from a dictionary."""
        data = _pad_environment_dict()
        result = PadEnvironment.from_dict(data=data)
        assert result.id == data["id"]
        assert result.pad_id == data["pad_id"]
        assert result.question_id == data["question_id"]
        assert result.example_question_id == data["example_question_id"]
        assert result.language == data["language"]
        assert len(result.file_contents) == len(data["file_contents"])
        assert result.created_at == data["created_at"]
        assert result.updated_at == data["updated_at"]


class TestCandidateInstruction:
    """Tests for ``CandidateInstruction``."""

    @staticmethod
    def test_from_dict() -> None:
        """A CandidateInstruction can be created from a dictionary."""
        data = _candidate_instruction_dict()
        result = CandidateInstruction.from_dict(data=data)
        assert result.instructions == data["instructions"]
        assert result.default_visible is True

    @staticmethod
    def test_model_validate_normalizes_null_visibility() -> None:
        """Pydantic parsing retains legacy null visibility handling."""
        result = CandidateInstruction.model_validate(
            obj={"instructions": "Do the thing", "default_visible": None},
        )
        assert result.default_visible is False


class TestTestCase:
    """Tests for ``TestCase``."""

    @staticmethod
    def test_from_dict() -> None:
        """A TestCase can be created from a dictionary."""
        data = _test_case_dict()
        result = TestCase.from_dict(data=data)
        assert result.id == data["id"]
        assert result.return_value == data["return_value"]
        assert result.visible == data["visible"]
        assert result.arguments == data["arguments"]


class TestCustomFile:
    """Tests for ``CustomFile``."""

    @staticmethod
    def test_from_dict() -> None:
        """A CustomFile can be created from a dictionary."""
        data = _custom_file_dict()
        result = CustomFile.from_dict(data=data)
        assert result.id == data["id"]
        assert result.title == data["title"]
        assert result.description == data["description"]
        assert result.filename == data["filename"]
        assert result.filesize == data["filesize"]


class TestQuestion:
    """Tests for ``Question``."""

    @staticmethod
    def test_from_dict() -> None:
        """A Question can be created from a dictionary."""
        data = _question_dict()
        result = Question.from_dict(data=data)
        assert result.id == data["id"]
        assert result.title == data["title"]
        assert result.owner_email == data["owner_email"]
        assert result.language == data["language"]
        assert result.description == data["description"]
        assert len(result.candidate_instructions) == len(
            data["candidate_instructions"],
        )
        assert result.contents == data["contents"]
        assert result.shared == data["shared"]
        assert result.used == data["used"]
        assert result.take_home == data["take_home"]
        assert result.test_cases_enabled == data["test_cases_enabled"]
        assert result.solution == data["solution"]
        assert result.pad_type == data["pad_type"]
        assert result.is_draft == data["is_draft"]
        assert result.author_name == data["author_name"]
        assert result.organization_name == data["organization_name"]
        assert len(result.custom_files) == len(data["custom_files"])
        assert result.created_at == data["created_at"]
        assert result.updated_at == data["updated_at"]
        assert (
            result.public_take_home_setting_id == _PUBLIC_TAKE_HOME_SETTING_ID
        )
        assert result.contents_for_test_cases == "test code"
        assert result.test_cases is not None
        assert len(result.test_cases) == 1
        assert result.custom_database is not None
        assert result.custom_database.title == "Products"
        assert result.custom_database.schema_json.tables[0].columns[0].pk
        assert result.ai_assist_custom_system_prompt == "Only provide hints."

    @staticmethod
    def test_model_validate_without_optional_fields() -> None:
        """Pydantic parsing accepts omitted optional response fields."""
        payload: dict[str, object] = dict(_question_dict())
        for field_name in (
            "language",
            "description",
            "contents",
            "solution",
            "public_take_home_setting_id",
            "contents_for_test_cases",
            "test_cases",
            "custom_database",
            "ai_assist_custom_system_prompt",
        ):
            _ = payload.pop(field_name)
        payload["candidate_instructions"] = [
            {"instructions": "Do the thing", "default_visible": None},
        ]

        result = Question.model_validate(obj=payload)

        assert result.language is None
        assert result.solution is None
        assert result.candidate_instructions[0].default_visible is False

    @staticmethod
    def test_from_dict_with_null_ai_assist_custom_system_prompt() -> None:
        """A Question can have no custom AI Assist system prompt."""
        data = _question_dict()
        data["ai_assist_custom_system_prompt"] = None
        result = Question.from_dict(data=data)
        assert result.ai_assist_custom_system_prompt is None

    @staticmethod
    def test_from_dict_without_ai_assist_custom_system_prompt() -> None:
        """A Question can omit its custom AI Assist system prompt."""
        data = _question_dict()
        del data["ai_assist_custom_system_prompt"]
        result = Question.from_dict(data=data)
        assert result.ai_assist_custom_system_prompt is None

    @staticmethod
    def test_from_dict_without_custom_database() -> None:
        """A Question can omit its empirically observed custom
        database.
        """
        data = _question_dict()
        del data["custom_database"]
        result = Question.from_dict(data=data)
        assert result.custom_database is None


class TestCustomDatabase:
    """Tests for ``CustomDatabase``."""

    @staticmethod
    def test_from_dict() -> None:
        """A custom database can be created from a dictionary."""
        data = _custom_database_dict()
        result = CustomDatabase.from_dict(data=data)
        assert result.id == data["id"]
        assert result.schema == data["schema"]  # pylint: disable=comparison-with-callable
        assert result.schema_json.arrangement == "horizontal"
        assert result.schema_json.tables[0].name == "products"
        assert result.schema_json.tables[0].columns[0].nn


class TestOrganizationUser:
    """Tests for ``OrganizationUser``."""

    @staticmethod
    def test_from_dict() -> None:
        """An OrganizationUser can be created from a dictionary."""
        data: OrganizationUserDict = {
            "email": "u@example.com",
            "name": "User",
            "teams": ["Backend"],
        }
        result = OrganizationUser.from_dict(data=data)
        assert result.email == data["email"]
        assert result.name == data["name"]
        assert result.teams == data["teams"]


class TestOrganizationStatsUser:
    """Tests for ``OrganizationStatsUser``."""

    @staticmethod
    def test_from_dict() -> None:
        """An OrganizationStatsUser can be created from a dictionary."""
        data: OrganizationStatsUserDict = {
            "email": "u@example.com",
            "name": "User",
            "pads_created": 5,
        }
        result = OrganizationStatsUser.from_dict(data=data)
        assert result.email == data["email"]
        assert result.name == data["name"]
        assert result.pads_created == data["pads_created"]


class TestQuota:
    """Tests for ``Quota``."""

    @staticmethod
    def test_from_dict() -> None:
        """A Quota can be created from a dictionary."""
        data: QuotaDict = {
            "trial_expires_at": "2024-01-01T00:00:00Z",
            "pads_used": 10,
            "quota_reset_at": "2024-02-01T00:00:00Z",
            "unlimited": False,
            "overages_enabled": True,
        }
        result = Quota.from_dict(data=data)
        assert result.trial_expires_at == data["trial_expires_at"]
        assert result.pads_used == data["pads_used"]
        assert result.quota_reset_at == data["quota_reset_at"]
        assert result.unlimited == data["unlimited"]
        assert result.overages_enabled == data["overages_enabled"]


class TestOrganization:
    """Tests for ``Organization``."""

    @staticmethod
    def test_from_dict() -> None:
        """An Organization can be created from a dictionary."""
        data: OrganizationDict = {
            "id": 123,
            "organization_name": "Acme",
            "user_count": 5,
            "users": [
                {"email": "u@example.com", "name": "User", "teams": ["BE"]},
            ],
            "organization_default_language": "python",
            "single_sign_on_supported": True,
            "single_sign_in_url": "https://sso.example.com",
            "teams": [_team_dict()],
            "child_organizations": [{"id": 456, "name": "Subsidiary"}],
        }
        result = Organization.from_dict(data=data)
        assert result.organization_name == data["organization_name"]
        assert result.user_count == data["user_count"]
        assert len(result.users) == len(data["users"])
        assert (
            result.organization_default_language
            == data["organization_default_language"]
        )
        assert (
            result.single_sign_on_supported == data["single_sign_on_supported"]
        )
        assert "single_sign_in_url" in data
        assert result.single_sign_in_url == data["single_sign_in_url"]
        assert len(result.teams) == len(data["teams"])
        assert "id" in data
        assert result.id == data["id"]
        assert "child_organizations" in data
        assert result.child_organizations == data["child_organizations"]

    @staticmethod
    def test_from_dict_without_sso_url_or_observed_fields() -> None:
        """An Organization can omit conditional and observed fields."""
        data: OrganizationDict = {
            "organization_name": "Acme",
            "user_count": 0,
            "users": [],
            "organization_default_language": "python",
            "single_sign_on_supported": False,
            "teams": [],
        }
        result = Organization.from_dict(data=data)
        assert result.single_sign_in_url is None
        assert result.id is None
        assert not bool(result.child_organizations)


class TestOrganizationStats:
    """Tests for ``OrganizationStats``."""

    @staticmethod
    def test_from_dict() -> None:
        """An OrganizationStats can be created from a
        dictionary.
        """
        data: OrganizationStatsDict = {
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-02-01T00:00:00Z",
            "pads_created": 42,
            "users": [
                {
                    "email": "u@example.com",
                    "name": "User",
                    "pads_created": 10,
                },
            ],
        }
        result = OrganizationStats.from_dict(data=data)
        assert result.start_time == data["start_time"]
        assert result.end_time == data["end_time"]
        assert result.pads_created == data["pads_created"]
        assert len(result.users) == len(data["users"])


def test_paginated_list_prev_page() -> None:
    """PaginatedList stores prev_page from construction."""
    page = PaginatedList(
        ["a"],
        total=2,
        next_page="https://example.com?page=2",
        prev_page="https://example.com?page=0",
    )
    assert page.prev_page == "https://example.com?page=0"
    assert page.next_page == "https://example.com?page=2"


def test_paginated_list_prev_page_defaults_none() -> None:
    """PaginatedList defaults prev_page to None."""
    page = PaginatedList(["a"], total=1)
    assert page.prev_page is None


class TestPaginatedList:
    """Tests for ``PaginatedList``."""

    @staticmethod
    def test_repr() -> None:
        """The string representation shows length, total, and next
        page.
        """
        pads: PaginatedList[str] = PaginatedList(
            ["a", "b"],
            total=10,
            next_page="https://example.com/page2",
        )
        assert (
            repr(pads) == "PaginatedList(len=2, total=10, "
            "next_page='https://example.com/page2')"
        )

    @staticmethod
    def test_repr_without_next_page() -> None:
        """The string representation shows None when there is no next page."""
        pads: PaginatedList[str] = PaginatedList([], total=0, next_page=None)
        assert repr(pads) == "PaginatedList(len=0, total=0, next_page=None)"


class TestScreenTestsPage:
    """Tests for ``ScreenTestsPage``."""

    @staticmethod
    def test_repr() -> None:
        """The string representation shows test count and pagination."""
        page = ScreenTestsPage(
            tests=[],
            pagination=ScreenPagination(
                start=0,
                limit=25,
                total=100,
                has_more_items=True,
                next_start=25,
            ),
        )
        assert repr(page) == (
            "ScreenTestsPage(tests=0, pagination=ScreenPagination("
            "start=0, limit=25, total=100, has_more_items=True, "
            "next_start=25))"
        )

    @staticmethod
    def test_repr_without_pagination() -> None:
        """The string representation shows None pagination when absent."""
        page = ScreenTestsPage(tests=[], pagination=None)
        assert repr(page) == "ScreenTestsPage(tests=0, pagination=None)"
