
from random import choice, randint, random, sample
from time import perf_counter
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.auths.models import CustomUser
from apps.blog.models import Category, Comment, Post, Tag


class Command(BaseCommand):
    """Command for filling the database with fake data."""

    help = "Fill the database with fake data."

    DEFAULT_USERS = 20
    DEFAULT_POSTS = 100
    DEFAULT_COMMENTS = 500

    SEED_PASSWORD = "TestPassword123!"
    EMAIL_DOMAIN = "example.com"

    STAFF_PROBABILITY = 0.10
    INACTIVE_PROBABILITY = 0.15
    PUBLISHED_PROBABILITY = 0.70
    EMPTY_CATEGORY_PROBABILITY = 0.10

    MAX_TAGS_PER_POST = 5
    POST_PARAGRAPHS = 3
    MIN_COMMENT_SENTENCES = 1
    MAX_COMMENT_SENTENCES = 3

    CATEGORY_NAMES = (
        "Python",
        "Django",
        "DevOps",
        "Databases",
        "Web Development",
        "Cybersecurity",
        "Artificial Intelligence",
        "Cloud Computing",
    )

    TAG_NAMES = (
        "python",
        "django",
        "fastapi",
        "rest-api",
        "postgresql",
        "sqlite",
        "docker",
        "kubernetes",
        "aws",
        "linux",
        "git",
        "github",
        "backend",
        "frontend",
        "javascript",
        "react",
        "testing",
        "security",
        "machine-learning",
        "tutorial",
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""

        parser.add_argument(
            "--users",
            type=int,
            default=self.DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=self.DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=self.DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    def __clear_data(self) -> None:
        """Delete existing data except superusers."""

        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()

        CustomUser.objects.exclude(
            is_superuser=True,
        ).delete()

    def __create_users(self, number_of_users: int) -> int:
        """Create users with unique emails."""

        fake = Faker()
        hashed_password: str = make_password(self.SEED_PASSWORD)

        used_emails: set[str] = {
            email.lower()
            for email in CustomUser.objects.values_list(
                "email", flat=True
            )
        }

        users_to_create: list[CustomUser] = []

        for _ in range(number_of_users):
            first_name: str = fake.first_name()
            last_name: str = fake.last_name()

            email_name: str = slugify(
                f"{first_name}.{last_name}"
            ).replace("-", ".")

            email: str = f"{email_name}@{self.EMAIL_DOMAIN}"
            suffix: int = 2

            while email in used_emails:
                email = (
                    f"{email_name}{suffix}@{self.EMAIL_DOMAIN}"
                )
                suffix += 1

            used_emails.add(email)

            is_active: bool = (
                random() >= self.INACTIVE_PROBABILITY
            )
            is_staff: bool = (
                is_active and random() < self.STAFF_PROBABILITY
            )

            users_to_create.append(
                CustomUser(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=is_active,
                    is_staff=is_staff,
                )
            )

        CustomUser.objects.bulk_create(users_to_create)

        return len(users_to_create)

    def __create_categories(self) -> int:
        """Create predefined categories."""

        existing_names: set[str] = set(
            Category.objects.values_list("name", flat=True)
        )
        existing_slugs: set[str] = set(
            Category.objects.values_list("slug", flat=True)
        )

        categories_to_create: list[Category] = []

        for name in self.CATEGORY_NAMES:
            slug: str = slugify(name)

            if name in existing_names or slug in existing_slugs:
                continue

            categories_to_create.append(
                Category(name=name, slug=slug)
            )
            existing_names.add(name)
            existing_slugs.add(slug)

        Category.objects.bulk_create(categories_to_create)

        return len(categories_to_create)

    def __create_tags(self) -> int:
        """Create predefined tags."""

        existing_names: set[str] = set(
            Tag.objects.values_list("name", flat=True)
        )
        existing_slugs: set[str] = set(
            Tag.objects.values_list("slug", flat=True)
        )

        tags_to_create: list[Tag] = []

        for name in self.TAG_NAMES:
            slug: str = slugify(name)

            if name in existing_names or slug in existing_slugs:
                continue

            tags_to_create.append(
                Tag(name=name, slug=slug)
            )
            existing_names.add(name)
            existing_slugs.add(slug)

        Tag.objects.bulk_create(tags_to_create)

        return len(tags_to_create)

    def __get_unique_slug(
        self,
        value: str,
        used_slugs: set[str],
        max_length: int,
    ) -> str:
        """Generate a unique slug."""

        base_slug: str = slugify(value)[:max_length].strip("-")
        base_slug = base_slug or "post"

        slug: str = base_slug
        suffix: int = 2

        while slug in used_slugs:
            suffix_text: str = f"-{suffix}"
            slug = (
                f"{base_slug[:max_length - len(suffix_text)]}"
                f"{suffix_text}"
            )
            suffix += 1

        used_slugs.add(slug)

        return slug

    def __create_posts(self, number_of_posts: int) -> int:
        """Create posts and attach random tags."""

        fake = Faker()

        users: list[CustomUser] = list(
            CustomUser.objects.all()
        )
        categories: list[Category] = list(
            Category.objects.all()
        )
        tags: list[Tag] = list(
            Tag.objects.all()
        )

        if not users and number_of_posts > 0:
            raise CommandError(
                "Cannot create posts: no users available."
            )

        used_slugs: set[str] = set(
            Post.objects.values_list("slug", flat=True)
        )
        slug_max_length: int = Post._meta.get_field(
            "slug"
        ).max_length

        posts_to_create: list[Post] = []
        tags_for_posts: list[list[Tag]] = []

        for _ in range(number_of_posts):
            title: str = fake.sentence()
            slug: str = self.__get_unique_slug(
                title,
                used_slugs,
                slug_max_length,
            )

            category: Category | None = None

            if (
                categories
                and random() >= self.EMPTY_CATEGORY_PROBABILITY
            ):
                category = choice(categories)

            status: str = (
                Post.StatusType.PUBLISHED
                if random() < self.PUBLISHED_PROBABILITY
                else Post.StatusType.DRAFT
            )

            posts_to_create.append(
                Post(
                    author=choice(users),
                    title=title,
                    slug=slug,
                    body="\n\n".join(
                        fake.paragraphs(nb=self.POST_PARAGRAPHS)
                    ),
                    category=category,
                    status=status,
                )
            )

            tags_count: int = randint(
                0,
                min(self.MAX_TAGS_PER_POST, len(tags)),
            )
            tags_for_posts.append(
                sample(tags, k=tags_count)
            )

        Post.objects.bulk_create(posts_to_create)

        for post, selected_tags in zip(
            posts_to_create, tags_for_posts
        ):
            post.tags.set(selected_tags)

        return len(posts_to_create)

    def __create_comments(self, number_of_comments: int) -> int:
        """Create comments for published posts only."""

        fake = Faker()

        users: list[CustomUser] = list(
            CustomUser.objects.all()
        )
        published_posts: list[Post] = list(
            Post.objects.filter(
                status=Post.StatusType.PUBLISHED,
            )
        )

        if number_of_comments > 0 and not users:
            raise CommandError(
                "Cannot create comments: no users available."
            )

        if number_of_comments > 0 and not published_posts:
            raise CommandError(
                "Cannot create comments: no published posts available."
            )

        comments_to_create: list[Comment] = []

        for _ in range(number_of_comments):
            sentences_count: int = randint(
                self.MIN_COMMENT_SENTENCES,
                self.MAX_COMMENT_SENTENCES,
            )

            comments_to_create.append(
                Comment(
                    post=choice(published_posts),
                    author=choice(users),
                    body=" ".join(
                        fake.sentence()
                        for _ in range(sentences_count)
                    ),
                )
            )

        Comment.objects.bulk_create(comments_to_create)

        return len(comments_to_create)

    def handle(self, *args: Any, **options: Any) -> None:
        """Command entry point."""

        start_time: float = perf_counter()

        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        for name, value in (
            ("users", users_count),
            ("posts", posts_count),
            ("comments", comments_count),
        ):
            if value < 0:
                raise CommandError(
                    f"--{name} cannot be negative."
                )

        with transaction.atomic():
            if clear:
                self.__clear_data()

            created_users: int = self.__create_users(
                users_count
            )
            created_categories: int = self.__create_categories()
            created_tags: int = self.__create_tags()
            created_posts: int = self.__create_posts(
                posts_count
            )
            created_comments: int = self.__create_comments(
                comments_count
            )

        duration: float = perf_counter() - start_time

        self.stdout.write(
            f'Users: {created_users} created'
        )

        self.stdout.write(
            f'Categories: {created_categories} created'
        )

        self.stdout.write(
            f'Tags: {created_tags} created'
        )

        self.stdout.write(
            f'Posts: {created_posts} created'
        )

        self.stdout.write(
            f'Comments: {created_comments} created'
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done in {duration:.2f} seconds"
            )
        )
