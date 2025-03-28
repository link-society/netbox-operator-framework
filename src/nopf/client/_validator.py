from typing import cast, Any, Callable, Hashable, Iterator, Mapping

from functools import wraps
from copy import deepcopy

from openapi_schema_validator.validators import SPECIFICATIONS
from openapi_schema_validator import OAS30Validator

from jsonschema.protocols import Validator
from jsonschema.validators import create
from jsonschema import ValidationError


type ValidatorCallback = Callable[
    [Validator, Any, Any, Mapping[Hashable, Any]],
    Iterator[ValidationError],
]


def _nullable_check_wrapper(func: ValidatorCallback) -> ValidatorCallback:
    @wraps(func)
    def wrapper(
        validator: Validator,
        value: Any,
        instance: Any,
        schema: Mapping[Hashable, Any],
    ) -> Iterator[ValidationError]:
        if instance is None and schema.get("nullable", False):
            return

        yield from func(validator, value, instance, schema)

    return wrapper


def _with_nullable_checks(
    validators: dict[str, ValidatorCallback],
) -> dict[str, ValidatorCallback]:
    for key in validators:
        if key in ["enum", "allOf", "anyOf", "oneOf", "$ref"]:
            validators[key] = _nullable_check_wrapper(validators[key])

    return validators


FixedOAS30Validator = create(
    meta_schema=SPECIFICATIONS.contents(
        "http://json-schema.org/draft-04/schema#",
    ),
    validators=cast(Any, _with_nullable_checks(deepcopy(OAS30Validator.VALIDATORS))),
    type_checker=OAS30Validator.TYPE_CHECKER,
    format_checker=OAS30Validator.FORMAT_CHECKER,
    id_of=lambda schema: cast(Mapping[str, Any], schema).get("id", ""),
)
