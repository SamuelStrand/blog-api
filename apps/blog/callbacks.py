
import json

from django.db.models import Count
from django.http import HttpRequest

from apps.auths.models import CustomUser
from apps.blog.models import Category, Comment, Post
from settings.conf import ENV_ID


def environment_callback(request: HttpRequest) -> list[str]:
    """Return environment name and label color"""

    if ENV_ID == "prod":
        return ["Production", "danger"]

    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> str:
    """Return number of draft posts"""

    return str(
        Post.objects.filter(
            status=Post.StatusType.DRAFT
        ).count()
    )


def dashboard_callback(
    request: HttpRequest,
    context: dict,
) -> dict:
    """Prepare dashboard statistics"""

    users_count: int = CustomUser.objects.count()

    published_count: int = Post.objects.filter(
        status=Post.StatusType.PUBLISHED
    ).count()

    drafts_count: int = Post.objects.filter(
        status=Post.StatusType.DRAFT
    ).count()

    comments_count: int = Comment.objects.count()

    total_posts: int = published_count + drafts_count

    published_percent: float = (
        round(published_count / total_posts * 100, 1)
        if total_posts
        else 0
    )
    drafts_percent: float = (
        round(drafts_count / total_posts * 100, 1)
        if total_posts
        else 0
    )

    categories = Category.objects.annotate(
        posts_count=Count("post")
    ).order_by("name")

    authors = CustomUser.objects.annotate(
        posts_count=Count("post")
    ).order_by("-posts_count", "email")[:5]

    chart_data: str = json.dumps(
        {
            "labels": [
                category.name for category in categories
            ],
            "datasets": [
                {
                    "label": "Posts",
                    "data": [
                        category.posts_count
                        for category in categories
                    ],
                    "backgroundColor": (
                        "var(--color-primary-600)"
                    ),
                },
            ],
        }
    )

    authors_table: dict = {
        "headers": ["Author", "Email", "Posts"],
        "rows": [
            [
                f"{author.first_name} {author.last_name}",
                author.email,
                author.posts_count,
            ]
            for author in authors
        ],
    }

    context.update(
        {
            "cards": [
                {
                    "title": "Total users",
                    "metric": users_count,
                },
                {
                    "title": "Published posts",
                    "metric": published_count,
                },
                {
                    "title": "Draft posts",
                    "metric": drafts_count,
                },
                {
                    "title": "Comments",
                    "metric": comments_count,
                },
            ],
            "posts_chart": chart_data,
            "authors_table": authors_table,
            "published_percent": published_percent,
            "drafts_percent": drafts_percent,
        }
    )

    return context
