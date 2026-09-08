"""Setup for Sybil."""

import json
import os
from collections.abc import Generator
from doctest import ELLIPSIS

import pytest
import respx
from sybil import Sybil
from sybil.parsers.rest import (
    ClearNamespaceParser,
    DocTestParser,
    PythonCodeBlockParser,
)

from tests.openapi_mock import JSONMapping, add_openapi_to_respx

_BASE_URL = "https://app.coderpad.io"


@pytest.fixture(name="mock_coderpad_api")
def fixture_mock_coderpad_api(
    request: pytest.FixtureRequest,
) -> Generator[respx.MockRouter]:
    """Provide a respx mock router backed by the OpenAPI spec."""
    openapi_spec_path = request.config.rootpath / "openapi.json"
    spec_text = openapi_spec_path.read_text(encoding="utf-8")
    openapi_spec: JSONMapping = json.loads(s=spec_text)  # ty: ignore[unsound-assignment]
    _ = os.environ.setdefault(key="CODERPAD_API_KEY", value="test-key")
    _ = os.environ.setdefault(
        key="CODERPAD_SCREEN_API_KEY", value="screen-key"
    )
    with respx.mock(
        base_url=_BASE_URL,
        assert_all_called=False,
    ) as mock_router:
        add_openapi_to_respx(
            mock_obj=mock_router,
            spec=openapi_spec,
            base_url=_BASE_URL,
        )
        _ = mock_router.get(
            url="https://www.codingame.com/assessment/api/v1.1/campaigns",
        ).respond(
            json=[{"id": 1, "name": "Example campaign"}],
        )
        _ = mock_router.post(
            url=(
                "https://www.codingame.com/assessment/api/v1.1/"
                "campaigns/1/actions/send"
            ),
        ).respond(
            json={
                "id": 11,
                "test_url": "https://test.example/invite",
            },
        )
        _ = mock_router.get(
            url="https://www.codingame.com/assessment/api/v1.1/tests",
        ).respond(
            json={
                "tests": [],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 0,
                    "has_more_items": False,
                    "next_start": None,
                },
            },
        )
        yield mock_router


pytest_collect_file = Sybil(
    parsers=[
        ClearNamespaceParser(),
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
    fixtures=["mock_coderpad_api"],
).pytest()
