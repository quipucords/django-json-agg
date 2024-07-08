"""post_factory utility for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable

from tests.models import Author
from tests.models import Post


if TYPE_CHECKING:
    from faker import Faker


def post_factory(
    faker: Faker,
    *,
    value_name: str,
    value_factory: Callable,
    number_of_posts: int = 20,
    number_of_authors: int = 10,
    plain_value: bool = False,
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
    if not plain_value:
        return posts_per_author_name
    return {
        author_name: list(post_dict.values())
        for author_name, post_dict in posts_per_author_name.items()
    }
