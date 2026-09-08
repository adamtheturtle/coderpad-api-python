"""OpenAPI-backed RESPX routes with request validation."""

from collections.abc import Callable, Iterator
from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qs

import httpx
import respx
from openapi_mock import add_openapi_to_respx as add_response_routes

_HTTP_METHODS = frozenset({"delete", "get", "patch", "post", "put"})
_URLENCODED = "application/x-www-form-urlencoded"
_MULTIPART = "multipart/form-data"

type JSONValue = (
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)
type JSONMapping = dict[str, JSONValue]


def add_openapi_to_respx(
    *,
    mock_obj: respx.MockRouter | respx.Router,
    spec: JSONMapping,
    base_url: str,
) -> None:
    """Add response routes and validate requests with their OpenAPI
    definitions.
    """
    initial_route_count = len(mock_obj.routes)
    add_response_routes(mock_obj=mock_obj, spec=spec, base_url=base_url)
    routes = list(mock_obj.routes)[initial_route_count:]

    for route, operation in zip(
        routes,
        _operations(spec=spec),
        strict=True,
    ):
        request_body_object = operation.get("requestBody")
        if not isinstance(request_body_object, dict):
            continue
        request_body: JSONMapping = request_body_object
        response = route.return_value
        assert response is not None
        _ = route.mock(
            side_effect=_request_validator(
                spec=spec,
                request_body=request_body,
                response=response,
            ),
        )


def _operations(*, spec: JSONMapping) -> Iterator[JSONMapping]:
    """Yield operations in the order used by ``openapi-mock``."""
    paths_object = spec.get("paths", {})
    assert isinstance(paths_object, dict)
    paths: JSONMapping = paths_object
    for path_item_object in paths.values():
        assert isinstance(path_item_object, dict)
        path_item: JSONMapping = path_item_object
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS:
                continue
            assert isinstance(operation, dict)
            yield operation


def _request_validator(
    *,
    spec: JSONMapping,
    request_body: JSONMapping,
    response: httpx.Response,
) -> Callable[[httpx.Request], httpx.Response]:
    """Build a RESPX callback that validates one operation's request
    body.
    """

    def validate_and_respond(request: httpx.Request) -> httpx.Response:
        """Validate the request and return the configured response."""
        _validate_request(
            request=request,
            request_body=request_body,
            spec=spec,
        )
        return response

    return validate_and_respond


def _validate_request(
    *,
    request: httpx.Request,
    request_body: JSONMapping,
    spec: JSONMapping,
) -> None:
    """Validate an HTTPX request against an OpenAPI form request body."""
    content_object = request_body.get("content", {})
    assert isinstance(content_object, dict)
    content: JSONMapping = content_object

    if not bool(request.content) and not bool(
        request_body.get("required", False)
    ):
        return

    content_type: str = request.headers.get(key="content-type", default="")
    media_type: str = content_type.partition(";")[0].lower()
    display_media_type = media_type if media_type != "" else "<missing>"
    assert media_type in content, (
        f"Unsupported content type {display_media_type!r} for "
        f"{request.method} {request.url.path}; expected one of "
        f"{sorted(content)}"
    )

    media_definition_object = content[media_type]
    assert isinstance(media_definition_object, dict)
    media_definition: JSONMapping = media_definition_object
    raw_schema = media_definition.get("schema", {})
    assert isinstance(raw_schema, dict)
    schema = _resolve_schema(spec=spec, raw_schema=raw_schema)
    fields = _form_fields(
        request=request,
        media_type=media_type,
        content_type=content_type,
    )
    properties_object = schema.get("properties", {})
    assert isinstance(properties_object, dict)
    properties: JSONMapping = properties_object
    schema_required = schema.get("required", [])
    raw_required = raw_schema.get("required", [])
    assert isinstance(schema_required, list)
    assert isinstance(raw_required, list)
    schema_required_names = {
        item for item in schema_required if isinstance(item, str)
    }
    raw_required_names = {
        item for item in raw_required if isinstance(item, str)
    }
    assert len(schema_required_names) == len(schema_required)
    assert len(raw_required_names) == len(raw_required)
    required = schema_required_names | raw_required_names
    missing = required - fields.keys()
    assert not bool(missing), (
        f"Missing required form fields for {request.method} "
        f"{request.url.path}: {sorted(missing)}"
    )
    if schema.get("additionalProperties", True) is False:
        unexpected = fields.keys() - properties.keys()
        assert not bool(unexpected), (
            f"Unexpected form fields for {request.method} "
            f"{request.url.path}: {sorted(unexpected)}"
        )
    for name, value in fields.items():
        property_object = properties.get(name)
        if not isinstance(property_object, dict):
            continue
        property_schema: JSONMapping = property_object
        if property_schema.get("format") == "binary":
            assert isinstance(value, bytes), f"{name!r} must be a file"
        else:
            assert isinstance(value, str), f"{name!r} must be text"
        allowed_values = property_schema.get("enum")
        if allowed_values is not None:
            assert isinstance(allowed_values, list)
            assert value in allowed_values, (
                f"Invalid value for form field {name!r}: {value!r}; "
                f"expected one of {allowed_values}"
            )


def _resolve_schema(
    *,
    spec: JSONMapping,
    raw_schema: JSONMapping,
) -> JSONMapping:
    """Resolve a local component schema reference."""
    reference = raw_schema.get("$ref")
    if reference is None:
        return raw_schema
    assert isinstance(reference, str)
    prefix = "#/components/schemas/"
    assert reference.startswith(prefix)
    components_object = spec.get("components", {})
    assert isinstance(components_object, dict)
    components: JSONMapping = components_object
    schemas_object = components.get("schemas", {})
    assert isinstance(schemas_object, dict)
    schemas: JSONMapping = schemas_object
    schema_object = schemas[reference.removeprefix(prefix)]
    assert isinstance(schema_object, dict)
    schema: JSONMapping = schema_object
    return schema


def _form_fields(
    *,
    request: httpx.Request,
    media_type: str,
    content_type: str,
) -> dict[str, str | bytes]:
    """Decode URL-encoded or multipart form fields from a request."""
    if media_type == _URLENCODED:
        parsed = parse_qs(
            qs=request.content.decode(),
            keep_blank_values=True,
            strict_parsing=True,
        )
        assert all(len(values) == 1 for values in parsed.values())
        return {name: values[0] for name, values in parsed.items()}

    assert media_type == _MULTIPART
    message = BytesParser(policy=policy.default).parsebytes(
        text=(
            b"Content-Type: "
            + content_type.encode()
            + b"\r\nMIME-Version: 1.0\r\n\r\n"
            + request.content
        ),
    )
    assert message.is_multipart()
    fields: dict[str, str | bytes] = {}
    for part in message.iter_parts():
        name = part.get_param(
            param="name",
            header="content-disposition",
        )
        assert isinstance(name, str)
        assert name not in fields
        payload = part.get_payload(decode=True)
        assert isinstance(payload, bytes)
        content_charset = part.get_content_charset()
        fields[name] = (
            payload
            if part.get_filename() is not None
            else payload.decode(
                encoding=(
                    content_charset if content_charset is not None else "utf-8"
                ),
            )
        )
    return fields
