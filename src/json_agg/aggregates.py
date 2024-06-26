"""JSON themed aggregates for Django."""

from collections.abc import Callable
from functools import partial
from typing import Any

from django.db import connection
from django.db.models import Aggregate
from django.db.models import Field
from django.db.models import Func
from django.db.models import JSONField


class JSONObjectAgg(Aggregate):
    """Aggregate as a JSON object."""

    template = "%(function)s(%(expressions)s)"
    output_field = JSONField(default=dict)

    def __init__(
        self,
        name_expression: Any,
        value_expression: Any,
        nested_output_field: Field = None,
        **kwargs,
    ):
        """Aggregate expressions as a JSON object / python dict.

        Args:
            name_expression: expression that will be used as JSON keys.
            value_expression: expression that will be used as JSON values.
            vendor_func: If provided, values will be wrapped with the specified
                function name in the given vendor. The actual keyword argument must
                replace "vendor" with the vendor name (e.g., "sqlite_func" for SQLite).
                This is particularly useful when "Cast" is not supported.
            nested_output_field: Django's model Field representing values inside the
                json.
            kwargs: same as the ones available in django's Aggregate.
        """
        self.function = {
            "sqlite": "JSON_GROUP_OBJECT",
            "postgresql": "JSONB_OBJECT_AGG",
        }[connection.vendor]
        if vendor_func := kwargs.get(f"{connection.vendor}_func"):
            value_expression = Func(value_expression, function=vendor_func)
        if nested_output_field and not isinstance(nested_output_field, Field):
            raise ValueError("'nested_output_field' must be a Django model Field.")
        self.nested_output_field = nested_output_field

        super().__init__(name_expression, value_expression, **kwargs)

    def _convert_nested_value(self, value, converter):
        if not value:
            return None
        return {k: converter(v) for k, v in value.items()}

    def _nested_db_converter(self, value, expression, connection, db_converter):
        converter = partial(db_converter, expression=expression, connection=connection)
        return self._convert_nested_value(value, converter)

    def _nested_to_python(self, value, expression, connection):
        return self._convert_nested_value(value, self.nested_output_field.to_python)

    def get_db_converters(self, connection: Any) -> list[Callable[..., Any]]:
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


class JSONArrayAgg(Aggregate):
    """Aggregate as JSON array."""

    template = "%(function)s(%(expressions)s)"
    output_field = JSONField(default=list)

    def __init__(self, expression, **kwargs):
        """Aggregate expression as a JSON array / python list.

        Args:
            expression: expression that will be used as array values.
            vendor_func: If provided, values will be wrapped with the specified
                function name in the given vendor. The actual keyword argument must
                replace "vendor" with the vendor name (e.g., "sqlite_func" for SQLite).
                This is particularly useful when "Cast" is not supported.
            kwargs: same as the ones available in django's Aggregate.
        """
        self.function = {
            "sqlite": "JSON_GROUP_ARRAY",
            "postgresql": "JSONB_AGG",
        }[connection.vendor]
        if vendor_func := kwargs.get(f"{connection.vendor}_func"):
            expression = Func(expression, function=vendor_func)
        super().__init__(expression, **kwargs)
