"""Test post_factory utility."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

import pytest

from tests.models import Post
from tests.post_factory import post_factory


if TYPE_CHECKING:
    from faker import Faker


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
