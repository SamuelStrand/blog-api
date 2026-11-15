from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import CustomUser as User
from apps.blog.models import Category, Comment, Post, Tag


NEWEST_POSTS_LIMIT = 5
POSTS_PER_PAGE = 10
EDIT_THRESHOLD_HOURS = 1
TOP_AUTHORS_LIMIT = 5
ROUND_DIGITS = 2
HOT_COMMENTS_MIN = 10
NORMAL_COMMENTS_MIN = 3
FEED_LIMIT = 50
TAGS_FEED_LIMIT = 20
UNCATEGORIZED_LABEL = "Uncategorized"
POPULARITY_HOT = "hot"
POPULARITY_NORMAL = "normal"
POPULARITY_QUIET = "quiet"


def categories_by_name() -> QuerySet[Category]:
    """Return all categories sorted by name."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Return published posts, newest first."""
    return Post.objects.filter(
        status=Post.StatusType.PUBLISHED,
    ).order_by("-created_at", "-pk")


def newest_published_posts() -> QuerySet[Post]:
    """Return the newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Return a post by slug, or None if it does not exist."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Count active users who are not staff members."""
    return User.objects.filter(is_active=True, is_staff=False).count()


def has_drafts() -> bool:
    """Check whether at least one draft post exists."""
    return Post.objects.filter(status=Post.StatusType.DRAFT).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """Return one page of published posts."""
    start: int = (page - 1) * POSTS_PER_PAGE
    end: int = start + POSTS_PER_PAGE
    return published_posts()[start:end]


def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Find posts containing a word in their title."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Find users with an email from the given domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Return posts without a category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Return categories with slugs from the given list."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Return posts created in the given month and year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Return posts created during the last given number of days."""
    return Post.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days),
    )


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Return posts created between two dates, inclusive."""
    return Post.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end,
    )


def author_published_posts(email: str) -> QuerySet[Post]:
    """Return published posts by an author with this email."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.StatusType.PUBLISHED,
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Return posts that have the specified tag."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Return comments on posts in the specified category."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Return unique users with at least one published post."""
    return User.objects.filter(
        post__status=Post.StatusType.PUBLISHED,
    ).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Return posts that have no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Return users who have never written a comment."""
    return User.objects.filter(comment__isnull=True)


def posts_with_both_tags(
    first_slug: str,
    second_slug: str,
) -> QuerySet[Post]:
    """Return posts containing both specified tags."""
    return (
        Post.objects.filter(tags__slug=first_slug)
        .filter(tags__slug=second_slug)
        .distinct()
    )


def search_posts(text: str) -> QuerySet[Post]:
    """Search for text in post titles or bodies."""
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text),
    )


def published_posts_missing_info() -> QuerySet[Post]:
    """Return published posts missing a category or tags."""
    return (
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .filter(Q(category__isnull=True) | Q(tags__isnull=True))
        .distinct()
    )


def edited_posts() -> QuerySet[Post]:
    """Return posts edited more than one hour after creation."""
    return Post.objects.filter(
        updated_at__gt=F("created_at") + timedelta(hours=EDIT_THRESHOLD_HOURS),
    )


def comments_by_post_author() -> QuerySet[Comment]:
    """Return comments written by the author of their own post."""
    return Comment.objects.filter(author_id=F("post__author_id"))


def comments_before_post() -> QuerySet[Comment]:
    """Return comments created before their parent posts."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))


def published_authors_emails() -> list[str]:
    """Return unique sorted emails of published post authors."""
    return list(
        User.objects.filter(post__status=Post.StatusType.PUBLISHED)
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Return published post titles, author emails and category names."""
    return list(
        Post.objects.filter(status=Post.StatusType.PUBLISHED).values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce(
                F("category__name"),
                Value(UNCATEGORIZED_LABEL),
                output_field=CharField(),
            ),
        )
    )


def posts_stats() -> dict[str, Any]:
    """Return post totals and the earliest and latest creation dates."""
    return Post.objects.aggregate(
        total=Count("pk"),
        published=Count(
            "pk",
            filter=Q(status=Post.StatusType.PUBLISHED),
        ),
        drafts=Count(
            "pk",
            filter=Q(status=Post.StatusType.DRAFT),
        ),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Return the average comment count of published posts."""
    statistics: dict[str, Any] = (
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .annotate(comment_count=Count("comment"))
        .aggregate(average=Avg("comment_count"))
    )
    return round(statistics["average"] or 0.0, ROUND_DIGITS)


def categories_with_post_count() -> QuerySet[Category]:
    """Return categories sorted by their total number of posts."""
    return Category.objects.annotate(
        post_count=Count("post"),
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Return categories with their published post counts."""
    return Category.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=Post.StatusType.PUBLISHED),
        ),
    )


def top_authors() -> QuerySet[User]:
    """Return the top authors by number of published posts."""
    return User.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=Post.StatusType.PUBLISHED),
        ),
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Return tags used by at least the given number of posts."""
    return (
        Tag.objects.annotate(post_count=Count("post"))
        .filter(post_count__gte=min_posts)
        .order_by("-post_count", "name")
    )


def posts_per_status() -> list[dict[str, Any]]:
    """Return post counts grouped by status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("pk"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Return users with accurate post and comment counts."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comment", distinct=True),
    )


def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Search users by a concatenated first and last name."""
    return User.objects.annotate(
        full_name=Concat(F("first_name"), Value(" "), F("last_name")),
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Return published post counts grouped by month."""
    return list(
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("pk"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Return posts with comment counts and popularity labels."""
    return Post.objects.annotate(
        comment_count=Count("comment"),
    ).annotate(
        popularity=Case(
            When(
                comment_count__gte=HOT_COMMENTS_MIN,
                then=Value(POPULARITY_HOT),
            ),
            When(
                comment_count__gte=NORMAL_COMMENTS_MIN,
                then=Value(POPULARITY_NORMAL),
            ),
            default=Value(POPULARITY_QUIET),
            output_field=CharField(),
        ),
    )


def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Return a tag by slug, creating it if it does not exist."""
    return Tag.objects.get_or_create(
        slug=slugify(name),
        defaults={"name": name},
    )


def publish_old_drafts(days: int) -> int:
    """Publish old drafts and update their modification time."""
    return Post.objects.filter(
        status=Post.StatusType.DRAFT,
        created_at__lt=timezone.now() - timedelta(days=days),
    ).update(
        status=Post.StatusType.PUBLISHED,
        updated_at=timezone.now(),
    )


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add a tag to every post of a category without duplicates."""
    post_ids: list[int] = list(
        Post.objects.filter(category__slug=category_slug).values_list(
            "pk", flat=True,
        )
    )
    tag: Tag = Tag.objects.get(slug=tag_slug)
    through = Post.tags.through
    through.objects.bulk_create(
        [
            through(post_id=post_id, tag_id=tag.pk)
            for post_id in post_ids
        ],
        ignore_conflicts=True,
    )
    return len(post_ids)


@transaction.atomic
def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move source category posts to the target and delete the source."""
    if source_slug == target_slug:
        raise ValueError("Source and target categories must be different.")

    source: Category = Category.objects.get(slug=source_slug)
    target: Category = Category.objects.get(slug=target_slug)
    moved_count: int = Post.objects.filter(category=source).update(
        category=target,
    )
    source.delete()
    return moved_count


def delete_inactive_users_comments() -> int:
    """Delete comments by inactive users and return the deleted count."""
    deleted_count, deleted_details = Comment.objects.filter(
        author__is_active=False,
    ).delete()
    return deleted_details.get("blog.Comment", deleted_count)


def published_feed() -> list[str]:
    """Return the newest published posts as formatted feed lines."""
    posts: QuerySet[Post] = published_posts().select_related(
        "author", "category",
    )[:FEED_LIMIT]
    return [
        (
            f"{post.title} | {post.author.email} | "
            f"{post.category.name if post.category else UNCATEGORIZED_LABEL}"
        )
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Return recent post titles and their prefetched tags."""
    posts: QuerySet[Post] = Post.objects.order_by(
        "-created_at", "-pk",
    ).prefetch_related("tags")[:TAGS_FEED_LIMIT]
    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Return each category and titles of its published posts."""
    categories: QuerySet[Category] = Category.objects.prefetch_related(
        Prefetch(
            "post_set",
            queryset=Post.objects.filter(
                status=Post.StatusType.PUBLISHED,
            ).order_by("-created_at", "-pk"),
            to_attr="published_posts",
        ),
    )
    return {
        category.name: [post.title for post in category.published_posts]
        for category in categories
    }


def posts_with_last_comment() -> QuerySet[Post]:
    """Return published posts with their newest comment body."""
    newest_comment: QuerySet[Comment] = Comment.objects.filter(
        post_id=OuterRef("pk"),
    ).order_by("-created_at", "-pk").values("body")[:1]
    return Post.objects.filter(
        status=Post.StatusType.PUBLISHED,
    ).annotate(last_comment=Subquery(newest_comment))


def posts_with_staff_comments() -> QuerySet[Post]:
    """Return posts that have at least one comment from a staff user."""
    staff_comments: QuerySet[Comment] = Comment.objects.filter(
        post_id=OuterRef("pk"),
        author__is_staff=True,
    )
    return Post.objects.filter(Exists(staff_comments))


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Return users whose newest post has draft status."""
    latest_post: QuerySet[Post] = Post.objects.filter(
        author_id=OuterRef("pk"),
    ).order_by("-created_at", "-pk").values("status")[:1]
    return User.objects.annotate(
        latest_post_status=Subquery(latest_post),
    ).filter(latest_post_status=Post.StatusType.DRAFT)


QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}