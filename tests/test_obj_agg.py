"""Test JSONObjectAgg aggregator."""

import pytest
from django.db.models import F

from json_agg import JSONObjectAgg
from tests.models import Author
from tests.models import Post


@pytest.mark.django_db
def test_aggregate_integer(faker):
    """Test JSONObjectAgg over a integer value (Post.year)."""
    expected_value_per_author_name = {
        faker.slug(): {
            faker.slug(): faker.pyint(min_value=1900, max_value=3500) for _ in range(20)
        }
        for _ in range(10)
    }

    for author_name, post_dict in expected_value_per_author_name.items():
        author = Author.objects.create(name=author_name)
        post_list = []
        for post_title, year in post_dict.items():
            post_list.append(Post(title=post_title, year=year, author=author))
        Post.objects.bulk_create(post_list)

    queryset = Author.objects.annotate(
        post_years=JSONObjectAgg(F("posts__title"), F("posts__year"))
    ).all()

    result_as_dict = {author.name: author.post_years for author in queryset}
    assert result_as_dict == expected_value_per_author_name
