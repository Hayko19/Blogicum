from django.db import models

from blog.querysets import PostQuerySet


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def category_published(self):
        return self.get_queryset().category_published()

    def published(self):
        return self.get_queryset().published()

    def published_up_to_now(self):
        return self.get_queryset().published_up_to_now()

    def available(self):
        return self.get_queryset().available()

    def with_comment_count(self):
        return self.get_queryset().with_comment_count()
