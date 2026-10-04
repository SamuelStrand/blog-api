from django.db import models

from apps.auths.models import CustomUser


class Category(models.Model):
    """
    Category of post
    """

    NAME_MAX_LEN = 100

    name = models.CharField(
        max_length=NAME_MAX_LEN,
        unique=True,
    )
    slug = models.SlugField(unique=True)


class Tag(models.Model):
    """
    Tag of post
    """

    NAME_MAX_LEN = 50

    name = models.CharField(
        max_length=NAME_MAX_LEN,
        unique=True
    )
    slug = models.SlugField(unique=True)


class Post(models.Model):
    """
    The Post model
    """

    class StatusType(models.TextChoices):
        DRAFT = "draft", "Draft",
        PUBLISHED = "published", "Published"

    TITLE_MAX_LEN = 200

    author = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=TITLE_MAX_LEN,
    )
    slug = models.SlugField(unique=True)
    body = models.TextField()
    category = models.ForeignKey(
        to=Category,
        on_delete=models.SET_NULL,
        null=True,
    )
    tags = models.ManyToManyField(
        to=Tag,
        blank=True
    )
    status = models.CharField(
        choices=StatusType.choices
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )


class Comment(models.Model):
    """
    Comment model
    """
    post = models.ForeignKey(
        to=Post,
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE
    )
    body = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )
