"""JSON themed aggregates for Django."""

from __future__ import annotations

import abc
from functools import partial
from typing import Any

from django.db import connection
from django.db.models import Aggregate
from django.db.models import Field
from django.db.models import Func
from django.db.models import JSONField
from django.db.models import Q


class JSONAggregateMixin(abc.ABC):
    """Mixin for JSON aggregators."""

    @abc.abstractmethod
    def _convert_nested_value(self, value: Any, converter: callable):
        """Convert nested values."""

    def __init__(
        self,
        *args,
        nested_output_field: Field = None,
        **kwargs,
    ):
        if nested_output_field and not isinstance(nested_output_field, Field):
            raise ValueError("'nested_output_field' must be a Django model Field.")
        self.nested_output_field = nested_output_field
        super().__init__(*args, **kwargs)

    def _nested_db_converter(self, value, expression, connection, db_converter):
        converter = partial(db_converter, expression=expression, connection=connection)
        return self._convert_nested_value(value, converter)

    def _nested_to_python(self, value, expression, connection):
        return self._convert_nested_value(value, self.nested_output_field.to_python)

    def get_db_converters(self, connection: Any) -> list[callable[..., Any]]:
        """Override Django's BaseExpression method to handle nested output fields."""
        converters = super().get_db_converters(connection)
        if not self.nested_output_field:
            return converters
        return (
            converters
            + [
                partial(self._nested_db_converter, db_converter=c)
                for c in self.nested_output_field.get_db_converters(connection)
            ]
            + [self._nested_to_python]
        )


class JSONObjectAgg(JSONAggregateMixin, Aggregate):
    """Aggregate as a JSON object.

    Args:
        name_expression: expression that will be used as JSON keys.
        value_expression: expression that will be used as JSON values.
        vendor_func: If provided, values will be wrapped with the specified
            function name in the given vendor. The actual keyword argument must
            replace "vendor" with the vendor name (e.g., "sqlite_func" for SQLite).
            This is particularly useful when "Cast" is not supported.
        nested_output_field: Django's model Field representing values inside the
            json.
        **kwargs: same as the ones available in django's Aggregate.
    """

    template = "%(function)s(%(expressions)s)"
    output_field = JSONField(default=dict)

    def __init__(
        self,
        name_expression: Any,
        value_expression: Any,
        **kwargs,
    ):
        self.function = {
            "sqlite": "JSON_GROUP_OBJECT",
            "postgresql": "JSONB_OBJECT_AGG",
        }[connection.vendor]
        if vendor_func := kwargs.get(f"{connection.vendor}_func"):
            value_expression = Func(value_expression, function=vendor_func)
        # key can't be NULL, so lets exclude it
        not_null_key_filter = Q(**{f"{name_expression}__isnull": False})
        filters = kwargs.pop("filter", None)
        if not filters:
            filters = not_null_key_filter
        else:
            filters = filters & not_null_key_filter
        super().__init__(
            name_expression,
            value_expression,
            filter=filters,
            **kwargs,
        )

    def _convert_nested_value(self, value, converter):
        if not value:
            return {}
        return {k: converter(v) for k, v in value.items()}

    @property
    def convert_value(self) -> callable:
        """Override BaseExpression.convert_value to handle json objects."""

        def _converter(value, expression, connection):
            if not value:
                return "{}"
            return value

        return _converter


class JSONArrayAgg(JSONAggregateMixin, Aggregate):
    """Aggregate as JSON array.

    Args:
        expression: expression that will be used as array values.
        vendor_func: If provided, values will be wrapped with the specified
            function name in the given vendor. The actual keyword argument must
            replace "vendor" with the vendor name (e.g., "sqlite_func" for SQLite).
            This is particularly useful when "Cast" is not supported.
        nested_output_field: Django's model Field representing values inside the
            json.
        **kwargs: same as the ones available in django's Aggregate.
    """

    template = "%(function)s(%(expressions)s)"
    output_field = JSONField(default=list)

    def __init__(self, expression: Any, **kwargs):
        self.function = {
            "sqlite": "JSON_GROUP_ARRAY",
            "postgresql": "JSONB_AGG",
        }[connection.vendor]
        if vendor_func := kwargs.get(f"{connection.vendor}_func"):
            expression = Func(expression, function=vendor_func)
        super().__init__(expression, **kwargs)

    def _convert_nested_value(self, value, converter):
        if not value:  # pragma: no cover
            return []
        return [converter(v) for v in value]
