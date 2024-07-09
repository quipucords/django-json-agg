"""Test JSONArrayAgg aggregator."""

from __future__ import annotations

import datetime
from functools import partial
from typing import TYPE_CHECKING

import pytest
from deepdiff import DeepDiff
from django.db.models import DateTimeField

from json_agg import JSONArrayAgg
from tests.models import Author
from tests.models import Post
from tests.post_factory import post_factory


if TYPE_CHECKING:
    from faker import Faker


@pytest.mark.django_db
def test_aggregate_integer(faker: Faker):
    """Test JSONArrayAgg over a integer value (Post.year)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="year",
        value_factory=partial(faker.pyint, min_value=1900, max_value=3500),
        plain_value=True,
    )

    queryset = Author.objects.annotate(json_array=JSONArrayAgg("posts__year")).all()

    result_as_dict = {author.name: author.json_array for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_text(faker: Faker):
    """Test JSONArrayAgg over a integer value (Post.content)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="content",
        value_factory=partial(faker.paragraph, variable_nb_sentences=True),
        plain_value=True,
    )

    queryset = Author.objects.annotate(json_array=JSONArrayAgg("posts__content")).all()

    result_as_dict = {author.name: author.json_array for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_datetime(faker: Faker, db_vendor: str):
    """Test JSONArrayAgg over a datetime value (Post.updated_at)."""
    kw = {}
    if db_vendor == "postgresql":
        # enforce tz for postgresql only - sqlite don't support it.
        kw = dict(tzinfo=datetime.timezone.utc)

    expected_value_per_author_name = post_factory(
        faker,
        value_name="updated_at",
        value_factory=partial(faker.date_time, **kw),
        plain_value=True,
    )

    queryset = Author.objects.annotate(
        json_array=JSONArrayAgg(
            "posts__updated_at", nested_output_field=DateTimeField()
        )
    ).all()

    result_as_dict = {author.name: author.json_array for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_json(faker: Faker):
    """Test JSONArrayAgg over a json value (Post.metadata)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="metadata",
        value_factory=partial(faker.pydict, allowed_types=(str, int)),
        plain_value=True,
    )
    # we can't use nested_output_field for JSONField because it would only work
    # for sqlite, which internally stores json as text. On postgres, data is
    # stored as jsonb, which is automatically translated to dict (maybe by psycopg2?).
    # This distinction on how those objects are stored internally breaks JSONField
    # default decoder, which doesn't expect dicts.
    queryset = Author.objects.annotate(
        json_array=JSONArrayAgg("posts__metadata", sqlite_func="json")
    ).all()

    result_as_dict = {author.name: author.json_array for author in queryset}
    diff = DeepDiff(result_as_dict, expected_value_per_author_name, ignore_order=True)
    assert diff == {}, diff


def test_raise_value_error_invalid_nested_output_field():
    """Ensure ValueError is raised if invalid type is used for nested_output_field."""
    with pytest.raises(ValueError):
        JSONArrayAgg("foo", nested_output_field=True)


@pytest.mark.django_db
def test_with_no_related_objects(faker: Faker):
    """Test JSONArrayAgg aggregating when there are no related objects."""
    author_name = faker.name()
    Author.objects.create(name=author_name)

    annotated_result = Author.objects.annotate(
        json_array=JSONArrayAgg("posts__title")
    ).first()

    # [None] might seem unexpected, postgresql indeed returns [null]
    assert annotated_result.json_array == [None]
    assert annotated_result.name == author_name


@pytest.mark.django_db
def test_no_related_objects_with_nested_output_field(faker: Faker):
    """Test JSONArrayAgg aggregating when there are no related objects."""
    author_name = faker.name()
    Author.objects.create(name=author_name)

    annotated_result = Author.objects.annotate(
        json_array=JSONArrayAgg(
            "posts__updated_at", nested_output_field=DateTimeField()
        )
    ).first()

    # [None] might seem unexpected, postgresql indeed returns [null]
    assert annotated_result.json_array == [None]
    assert annotated_result.name == author_name


@pytest.mark.django_db
def test_null_value(faker: Faker):
    """Test JSONArrayAgg aggregating when related object has null value."""
    author_name = faker.name()
    post_title = faker.slug()
    author = Author.objects.create(name=author_name)
    Post.objects.create(title=post_title, author=author, content=None)

    annotated_result = Author.objects.annotate(
        json_array=JSONArrayAgg("posts__content")
    ).first()

    assert annotated_result.json_array == [None]
    assert annotated_result.name == author_name


@pytest.mark.django_db
def test_null_value_with_nested_output_field(faker: Faker):
    """Test JSONArrayAgg aggregating when related object has null value."""
    author_name = faker.name()
    post_title = faker.slug()
    author = Author.objects.create(name=author_name)
    Post.objects.create(title=post_title, author=author, updated_at=None)

    annotated_result = Author.objects.annotate(
        json_array=JSONArrayAgg(
            "posts__updated_at", nested_output_field=DateTimeField()
        )
    ).first()

    assert annotated_result.json_array == [None]
    assert annotated_result.name == author_name
