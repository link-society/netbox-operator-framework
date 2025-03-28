from typing import Any

from copy import deepcopy

from httpx import AsyncClient as HTTPClient, Response
from jsonschema import ValidationError  # type: ignore

from ._validator import FixedOAS30Validator


class Operation:
    def __init__(
        self,
        client: HTTPClient,
        method: str,
        path: str,
        spec: dict[str, Any],
        root_schema: dict[str, Any],
    ) -> None:
        self.name = spec["operationId"]
        self.__doc__ = spec.get("description", "")

        self._client = client
        self._method = method
        self._path = path
        self._spec = spec
        self._root_schema = root_schema

    async def __call__(
        self,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Response:
        if params is None:
            params = {}

        path_params: dict[str, str] = {}
        query_params: dict[str, list[str]] = {}

        for param_spec in self._spec.get("parameters", []):
            param_name = param_spec["name"]
            required = param_spec.get("required", False)

            if required and param_name not in params:
                raise ValueError(
                    f"Operation({self.name}): Missing parameter: {param_name}"
                )

            if param_name in params:
                expected_param_schema = deepcopy(param_spec["schema"])
                expected_param_schema["components"] = self._root_schema["components"]
                param_value = params[param_name]

                try:
                    validator = FixedOAS30Validator(expected_param_schema)
                    validator.validate(param_value)

                except ValidationError as err:
                    raise ValueError(
                        f"Operation({self.name}): Invalid parameter: {param_name}"
                    ) from err

                match param_spec["in"]:
                    case "path":
                        path_params[param_name] = param_value

                    case "query":
                        if not isinstance(param_value, list):
                            param_value = [param_value]

                        for value in param_value:
                            query_params.setdefault(param_name, []).append(value)

        path = self._path.format(**path_params)
        response = await self._client.request(
            self._method,
            path,
            params=query_params,
            json=body,
        )
        await response.aread()

        status_code = f"{response.status_code}"

        if status_code in self._spec["responses"]:
            response_spec = self._spec["responses"][status_code]
            response_schema = deepcopy(
                response_spec.get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )

            if response_schema:
                response_schema["components"] = self._root_schema["components"]
                response_data = response.json()

                try:
                    validator = FixedOAS30Validator(response_schema)
                    validator.validate(response_data)

                except ValidationError as err:
                    raise ValueError(
                        f"Operation({self.name}): Invalid response"
                    ) from err

        return response
