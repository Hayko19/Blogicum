from django.db import models
from django.db.models import Count
from django.utils.timezone import now


class PostQuerySet(models.QuerySet):
    def category_published(self):
        return self.filter(category__is_published=True)

    def published(self):
        return self.filter(is_published=True)

    def published_up_to_now(self):
        return self.filter(pub_date__lte=now())

    def available(self):
        return self.category_published().published().published_up_to_now()

    def with_comment_count(self):
        return self.annotate(comment_count=Count('comments'))
