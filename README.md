# Django JSON Agg

[![PyPI](https://img.shields.io/pypi/v/django-json-agg.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/django-json-agg.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/django-json-agg)][pypi status]
[![License](https://img.shields.io/pypi/l/django-json-agg)][license]

[![Read the documentation at https://django-json-agg.readthedocs.io/](https://img.shields.io/readthedocs/django-json-agg/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/quipucords/django-json-agg/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/quipucords/django-json-agg/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Ruff codestyle][ruff badge]][ruff project]

[pypi status]: https://pypi.org/project/django-json-agg/
[read the docs]: https://django-json-agg.readthedocs.io/
[tests]: https://github.com/quipucords/django-json-agg/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/quipucords/django-json-agg
[pre-commit]: https://github.com/pre-commit/pre-commit
[ruff badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff project]: https://github.com/charliermarsh/ruff

## Features

Exposes JSON related aggregation functions (like postgres's `json_object_agg` and `json_agg`) as Django Aggregate objects.

## Requirements

Django version 4.2. It might work with other versions, but it is not tested with them.
For now only sqlite and postgresql databases are supported.

## Installation

You can install _Django JSON Agg_ via [pip] from [PyPI]:

```console
$ pip install django-json-agg
```

And add it to Django settings `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # other apps
    'json_agg',
]
```

## Usage

Let's assume you have the following models

```python
class Post(models.Model):
    """Model representing a blog post."""

    title = models.CharField(max_length=100, null=True, unique=True)
    content = models.TextField(null=True)
    author = models.ForeignKey(
        "tests.Author", related_name="posts", on_delete=models.CASCADE
    )


class Author(models.Model):
    """Model representing a blog post Author."""
    name = models.CharField(max_length=100)
```

If you want all author objects and their posts formatted as a dict, with
title as key and content as value, you can run the following

```python
from json_agg import JSONObjectAgg

from .models import Author


queryset = Author.objects.annotate(
    post_map=JSONObjectAgg("posts__title", "posts__content")
).all()
```

In the example above, `Author` instances would have the attribute `post_map`, which would a
a dict.

A similar aggregator, `JSONArrayAgg`, is also available.

Please see the [reference] for details.

## Is this project for me?

django-json-agg aims to improve the ergonomics for aggregating data as dicts or lists
while still keeping other model instances. All that in a single query. One might argue
it also adds some efficiency by building the dict/list in the database, instead of python side.

However, reliance on django-json-agg and JSON data structures in general for storing
"relational" data may be an anti-pattern or an indicator of a problematic or suboptimal
database schema design. Your time may be better spent refactoring your models to use
more native primitive data types and relations (foreign keys, indexes, etc).

Without this project, a similar result to the example above could be achieved with:

```python
from collections import defaultdict

from json_agg import JSONObjectAgg

from .models import Author, Post


posts = Post.objects.values_list("author_id", "title", "content")
posts_per_author = defaultdict(dict)
for author_id, title, content in posts:
    posts_per_author[author_id][title] = content

authors = Author.objects.all()
# accessing posts per author
for author in Author.objects.all():
    author_posts = posts_per_author[author.id]
```

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [GPL 3.0 license][license],
_Django JSON Agg_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/quipucords/django-json-agg/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/quipucords/django-json-agg/blob/main/LICENSE
[contributor guide]: https://github.com/quipucords/django-json-agg/blob/main/CONTRIBUTING.md
[reference]: https://django-json-agg.readthedocs.io/en/latest/reference.html
