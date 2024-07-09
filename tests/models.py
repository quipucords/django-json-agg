"""models for testing json_agg."""

from datetime import datetime

from django.db import models


class Post(models.Model):
    """Model representing a blog post."""

    title = models.CharField(max_length=100)
    year = models.IntegerField(default=datetime.now().year)
    updated_at = models.DateTimeField(null=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    author = models.ForeignKey(
        "tests.Author", related_name="posts", on_delete=models.CASCADE
    )


class Author(models.Model):
    """Model representing a blog post Author."""

    name = models.CharField(max_length=100)
