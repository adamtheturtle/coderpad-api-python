"""Tests for the request-validating OpenAPI mock."""

import httpx
import pytest
import respx
from respx.models import AllMockedAssertionError

from tests.openapi_mock import JSONMapping, add_openapi_to_respx

_QUESTIONS_URL = "https://app.coderpad.io/api/questions/"


class TestOpenAPIRequestValidation:
    """Tests for OpenAPI request-contract validation."""

    @staticmethod
    def test_supports_inline_extensible_schema() -> None:
        """An inline schema may allow fields beyond declared
        properties.
        """
        spec: JSONMapping = {
            "paths": {
                "/widgets/": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {"type": "object"},
                                },
                            },
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "example": {"status": "OK"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
        with respx.mock(
            base_url="https://example.com",
            assert_all_called=False,
        ) as mock_router:
            add_openapi_to_respx(
                mock_obj=mock_router,
                spec=spec,
                base_url="https://example.com",
            )
            response = httpx.post(
                url="https://example.com/widgets/",
                data={"extension": "value"},
            )
        assert response.json() == {"status": "OK"}

    @staticmethod
    @pytest.mark.parametrize(
        argnames=("method", "url"),
        argvalues=[
            ("PATCH", _QUESTIONS_URL),
            ("POST", "https://app.coderpad.io/api/unknown/"),
        ],
    )
    def test_rejects_unmatched_method_or_path(
        mock_coderpad_api: object,
        method: str,
        url: str,
    ) -> None:
        """A method and path must match an OpenAPI operation."""
        del mock_coderpad_api
        with pytest.raises(expected_exception=AllMockedAssertionError):
            _ = httpx.request(method=method, url=url)

    @staticmethod
    def test_rejects_unsupported_content_type(
        mock_coderpad_api: object,
    ) -> None:
        """The content type must be declared by the operation."""
        del mock_coderpad_api
        with pytest.raises(
            expected_exception=AssertionError,
            match="Unsupported content type 'application/json'",
        ):
            _ = httpx.post(
                url=_QUESTIONS_URL,
                json={
                    "question[title]": "FizzBuzz",
                    "question[language]": "python",
                },
            )

    @staticmethod
    def test_rejects_missing_required_field(
        mock_coderpad_api: object,
    ) -> None:
        """Required form fields must be present."""
        del mock_coderpad_api
        with pytest.raises(
            expected_exception=AssertionError,
            match=r"Missing required form fields.*question\[language\]",
        ):
            _ = httpx.post(
                url=_QUESTIONS_URL,
                data={"question[title]": "FizzBuzz"},
            )

    @staticmethod
    def test_rejects_unexpected_field(
        mock_coderpad_api: object,
    ) -> None:
        """Form fields not declared by the schema are rejected."""
        del mock_coderpad_api
        with pytest.raises(
            expected_exception=AssertionError,
            match=r"Unexpected form fields.*question\[titel\]",
        ):
            _ = httpx.post(
                url=_QUESTIONS_URL,
                data={
                    "question[title]": "FizzBuzz",
                    "question[language]": "python",
                    "question[titel]": "misspelled",
                },
            )

    @staticmethod
    def test_rejects_invalid_field_value(
        mock_coderpad_api: object,
    ) -> None:
        """A form value must satisfy its field schema."""
        del mock_coderpad_api
        with pytest.raises(
            expected_exception=AssertionError,
            match=r"Invalid value for form field 'ended'",
        ):
            _ = httpx.put(
                url="https://app.coderpad.io/api/pads/ABC1234",
                data={"ended": "yes"},
            )
