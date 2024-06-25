"""Test JSONObjectAgg aggregator."""

from __future__ import annotations

import datetime
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING

import pytest
from django.db.models import DateTimeField

from json_agg import JSONObjectAgg
from tests.models import Author
from tests.models import Post


if TYPE_CHECKING:
    from typing import Callable

    from faker import Faker


def post_factory(
    faker: Faker,
    *,
    value_name: str,
    value_factory: Callable,
    number_of_posts: int = 20,
    number_of_authors: int = 10,
):
    """Factory to create author and posts in this test module."""
    posts_per_author_name = {
        faker.slug(): {faker.slug(): value_factory() for _ in range(number_of_posts)}
        for _ in range(number_of_authors)
    }

    for author_name, post_dict in posts_per_author_name.items():
        author = Author.objects.create(name=author_name)
        post_list = []
        for post_title, value in post_dict.items():
            post_list.append(
                Post(title=post_title, author=author, **{value_name: value})
            )
        Post.objects.bulk_create(post_list)
    return posts_per_author_name


@pytest.mark.django_db
def test_post_factory(faker: Faker):
    """Test helper function "post_factory"."""

    class _DummyFactory:
        _dummy_value = 0

        def __call__(self):
            self._dummy_value += 1
            return self._dummy_value

    posts_per_author = post_factory(
        faker,
        value_name="year",
        value_factory=_DummyFactory(),
        number_of_authors=2,
        number_of_posts=2,
    )
    assert isinstance(posts_per_author, dict)
    assert len(posts_per_author) == 2
    assert all(isinstance(posts, dict) for posts in posts_per_author.values())
    assert all(len(posts) == 2 for posts in posts_per_author.values())

    expected_values = [1, 2, 3, 4]

    # since author name and post title are random, let's only check expected values
    assert set(
        chain.from_iterable(posts.values() for posts in posts_per_author.values())
    ) == set(expected_values)

    # ensure the values were persisted in db
    qs = Post.objects.order_by("year").values_list("year").all()
    assert list(chain.from_iterable(qs)) == expected_values


@pytest.mark.django_db
def test_aggregate_integer(faker: Faker):
    """Test JSONObjectAgg over a integer value (Post.year)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="year",
        value_factory=partial(faker.pyint, min_value=1900, max_value=3500),
    )

    queryset = Author.objects.annotate(
        post_years=JSONObjectAgg("posts__title", "posts__year")
    ).all()

    result_as_dict = {author.name: author.post_years for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_text(faker: Faker):
    """Test JSONObjectAgg over a integer value (Post.content)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="content",
        value_factory=partial(faker.paragraph, variable_nb_sentences=True),
    )

    queryset = Author.objects.annotate(
        post_content=JSONObjectAgg("posts__title", "posts__content")
    ).all()

    result_as_dict = {author.name: author.post_content for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_datetime(faker: Faker, db_vendor: str):
    """Test JSONObjectAgg over a datetime value (Post.updated_at)."""
    kw = {}
    if db_vendor == "postgresql":
        # enforce tz for postgresql only - sqlite don't support it.
        kw = dict(tzinfo=datetime.UTC)

    expected_value_per_author_name = post_factory(
        faker,
        value_name="updated_at",
        value_factory=partial(faker.date_time, **kw),
    )

    queryset = Author.objects.annotate(
        post_updated_at=JSONObjectAgg(
            "posts__title", "posts__updated_at", nested_output_field=DateTimeField()
        )
    ).all()

    result_as_dict = {author.name: author.post_updated_at for author in queryset}
    assert result_as_dict == expected_value_per_author_name


@pytest.mark.django_db
def test_aggregate_json(faker: Faker):
    """Test JSONObjectAgg over a json value (Post.metadata)."""
    expected_value_per_author_name = post_factory(
        faker,
        value_name="metadata",
        value_factory=partial(faker.pydict, allowed_types=(str, int)),
    )
    # we can't use nested_output_field for JSONField because it would only work
    # for sqlite, which internally stores json as text. On postgres, data is
    # stored as jsonb, which is automatically translated to dict (maybe by psycopg2?).
    # This distinction on how those objects are stored internally breaks JSONField
    # default decoder, which doesn't expect dicts.
    queryset = Author.objects.annotate(
        post_metadata=JSONObjectAgg(
            "posts__title",
            "posts__metadata",
            # nested_output_field=JSONField(),
            sqlite_func="json",
        )
    ).all()

    result_as_dict = {author.name: author.post_metadata for author in queryset}
    assert result_as_dict == expected_value_per_author_name
