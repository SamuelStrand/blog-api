from datetime import timedelta
from typing import Any

from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import CustomUser
from apps.blog.models import Comment, Post
from apps.blog.queries import QUERIES


SAMPLE_ARGUMENTS: dict[int, dict[str, Any]] = {
    7: {"page": 1},
    9: {"domain": "example.com"},
    11: {"slugs": ["python", "django"]},
    13: {"days": 365},
    14: {
        "start": timezone.localdate() - timedelta(days=365),
        "end": timezone.localdate(),
    },
    34: {"min_posts": 1},
    40: {"name": "Django ORM"},
    41: {"days": 30},
    42: {
        "category_slug": "django",
        "tag_slug": "python",
    },
    43: {
        "source_slug": "django",
        "target_slug": "python",
    },
}


class Command(BaseCommand):
    """Command for running Django ORM queries."""

    help = "Run Django ORM homework queries."

    ROWS_LIMIT = 5
    MUTATING_QUERIES = (40, 41, 42, 43, 44)

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""

        parser.add_argument(
            "--number",
            type=int,
            default=None,
            help="Run specified query number",
        )

        parser.add_argument(
            "--sql",
            action="store_true",
            help="Show executed SQL queries",
        )

    def __get_arguments(self, number: int) -> dict[str, Any]:
        """Return sample arguments for specified query."""

        arguments: dict[str, Any] = dict(
            SAMPLE_ARGUMENTS.get(number, {})
        )

        if number in (4, 8, 12, 15, 22):
            post = Post.objects.filter(
                status=Post.StatusType.PUBLISHED
            ).select_related(
                "author"
            ).order_by(
                "pk"
            ).first()

            if not post:
                raise CommandError(
                    "No published posts. Run seed first."
                )

            if number == 4:
                arguments["slug"] = post.slug

            elif number == 8:
                arguments["word"] = post.title.split()[0].strip(
                    ".,!?"
                )

            elif number == 12:
                arguments["year"] = post.created_at.year
                arguments["month"] = post.created_at.month

            elif number == 15:
                arguments["email"] = post.author.email

            elif number == 22:
                arguments["text"] = post.title.split()[0].strip(
                    ".,!?"
                )

        elif number == 16:
            tag_slug = Post.objects.filter(
                tags__isnull=False
            ).values_list(
                "tags__slug",
                flat=True,
            ).first()

            arguments["tag_slug"] = tag_slug or "python"

        elif number == 17:
            category_slug = Comment.objects.filter(
                post__category__isnull=False
            ).values_list(
                "post__category__slug",
                flat=True,
            ).first()

            arguments["category_slug"] = (
                category_slug or "python"
            )

        elif number == 21:
            post = Post.objects.annotate(
                tags_total=Count("tags")
            ).filter(
                tags_total__gte=2
            ).first()

            if not post:
                raise CommandError(
                    "No posts with at least two tags."
                )

            slugs = list(
                post.tags.values_list(
                    "slug",
                    flat=True,
                )[:2]
            )

            arguments["first_slug"] = slugs[0]
            arguments["second_slug"] = slugs[1]

        elif number == 37:
            user = CustomUser.objects.exclude(
                first_name=""
            ).first()

            arguments["text"] = (
                user.first_name if user else "a"
            )

        return arguments

    def __format_row(
        self,
        row: Any,
        annotation_names: tuple[str, ...],
    ) -> str:
        """Format result row and annotation values."""

        if isinstance(row, Model):
            value = (
                getattr(row, "title", None)
                or getattr(row, "name", None)
                or getattr(row, "email", None)
                or getattr(row, "body", None)
                or row.pk
            )

            annotations: dict[str, Any] = {
                name: getattr(row, name)
                for name in annotation_names
            }

            if annotations:
                return f"{value} {annotations}"

            return str(value)

        return str(row)

    def __run_query(
        self,
        number: int,
        show_sql: bool,
    ) -> None:
        """Run query and capture its SQL statements."""

        function = QUERIES[number]
        arguments = self.__get_arguments(number)

        annotation_names: tuple[str, ...] = ()

        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)

            if isinstance(result, QuerySet):
                annotation_names = tuple(
                    result.query.annotations
                )
                result = list(result)

        sql_count: int = len(context.captured_queries)

        self.stdout.write(
            f"#{number} {function.__name__} — "
            f"{sql_count} SQL queries"
        )

        if show_sql:
            for query in context.captured_queries:
                self.stdout.write(query["sql"])

        if isinstance(result, list):
            for row in result[:self.ROWS_LIMIT]:
                self.stdout.write(
                    f"  {self.__format_row(row, annotation_names)}"
                )

            self.stdout.write(
                f"  ({len(result)} rows)"
            )

        else:
            self.stdout.write(
                f"  {self.__format_row(result, annotation_names)}"
            )

        self.stdout.write("")

    def handle(self, *args: Any, **options: Any) -> None:
        """Command entry point."""

        number: int | None = options["number"]
        show_sql: bool = options["sql"]

        if number is not None and number not in QUERIES:
            raise CommandError(
                f"Query #{number} does not exist."
            )

        if number is not None:
            numbers: list[int] = [number]
        else:
            numbers = [
                query_number
                for query_number in QUERIES
                if query_number not in self.MUTATING_QUERIES
            ]

        for query_number in numbers:
            self.__run_query(
                number=query_number,
                show_sql=show_sql,
            )
