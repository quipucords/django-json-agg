"""JSON themed aggregates for Django."""

from django.db import connection
from django.db.models import Aggregate
from django.db.models import Func
from django.db.models import JSONField


class JSONObjectAgg(Aggregate):
    """Aggregate as a JSON object."""

    template = "%(function)s(%(expressions)s)"
    output_field = JSONField(default=dict)

    def __init__(self, name_expression, value_expression, **kwargs):
        """Aggregate expressions as a JSON object / python dict.

        Args:
            name_expression: expression that will be used as JSON keys.
            value_expression: expression that will be used as JSON values.
            vendor_func: If provided, values will be wrapped with the specified
                function name in the given vendor. The actual keyword argument must
                replace "vendor" with the vendor name (e.g., "sqlite_func" for SQLite).
                This is particularly useful when "Cast" is not supported.
            kwargs: same as the ones available in django's Aggregate.
        """
        self.function = {
            "sqlite": "JSON_GROUP_OBJECT",
            "postgresql": "JSONB_OBJECT_AGG",
        }[connection.vendor]

        if vendor_func := kwargs.get(f"{connection.vendor}_func"):
            value_expression = Func(value_expression, function=vendor_func)
        super().__init__(name_expression, value_expression, **kwargs)


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
