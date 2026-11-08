from django.contrib import admin
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateTimeFilter, AutocompleteSelectFilter, MultipleRelatedDropdownFilter, \
    RelatedDropdownFilter, ChoicesDropdownFilter
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from apps.blog.models import Category, Comment, Post, Tag


class CategoryPostsSection(TableSection):
    """Expandable table of posts in a category."""

    verbose_name = "Category posts"
    related_name = "post_set"
    fields = ["title", "status", "created_at"]


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Category model admin configuration class."""

    list_display = (
        "name",
        "slug",
        "posts_count",
    )
    search_fields = ("name",)
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_sections = [CategoryPostsSection]
    list_per_page = 20

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate categories with their post counts."""

        return (
            super()
            .get_queryset(request)
            .annotate(posts_total=Count("post"))
            .prefetch_related("post_set")
        )

    @display(description="Posts", ordering="posts_total")
    def posts_count(self, obj: Category) -> int:
        """Return number of posts."""

        return obj.posts_total


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Tag model admin configuration class."""

    list_display = (
        "name",
        "slug",
        "posts_count",
    )
    search_fields = ("name",)
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_per_page = 20

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate tags with their post counts."""

        return (
            super()
            .get_queryset(request)
            .annotate(posts_total=Count("post"))
        )

    @display(description="Posts", ordering="posts_total")
    def posts_count(self, obj: Tag) -> int:
        """Return number of posts."""

        return obj.posts_total


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """Comment model admin configuration class."""

    BODY_PREVIEW_LENGTH = 60

    list_display = (
        "post_title",
        "author",
        "body_preview",
        "created_at",
    )
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = (
        "body",
        "author__email",
        "post__title",
    )
    autocomplete_fields = (
        "post",
        "author",
    )
    list_select_related = (
        "post",
        "author",
    )
    readonly_fields = ("created_at",)
    list_per_page = 20

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        """Return post title."""

        return obj.post.title

    @display(description="Body")
    def body_preview(self, obj: Comment) -> str:
        """Return shortened comment body."""

        body: str = obj.body[:self.BODY_PREVIEW_LENGTH]

        if len(obj.body) > self.BODY_PREVIEW_LENGTH:
            return f"{body}..."

        return body


class PostCommentsSection(TableSection):
    """Expandable table of post comments."""

    verbose_name = "Post comments"
    related_name = "comment_set"
    fields = ["author", "body", "created_at"]


class CommentInline(TabularInline):
    """Inline comments on the post edit page."""

    model = Comment
    tab = True
    per_page = 10
    extra = 0
    show_change_link = True

    autocomplete_fields = ("author",)
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """Post model admin configuration class."""

    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    )
    list_display_links = ("post_header",)

    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    search_fields = (
        "title",
        "body",
        "author__email",
    )
    autocomplete_fields = (
        "author",
        "category",
        "tags",
    )
    prepopulated_fields = {
        "slug": ("title",),
    }

    list_select_related = (
        "author",
        "category",
    )
    list_per_page = 20

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_sections = [PostCommentsSection]
    inlines = [CommentInline]

    warn_unsaved_form = True
    show_view_on_site = False

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
    }

    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": (
                    "title",
                    "slug",
                    "body",
                ),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": (
                    "category",
                    "tags",
                    "status",
                ),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": (
                    "author",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    actions = (
        "publish_selected",
        "move_to_drafts",
    )
    actions_row = ["toggle_status"]
    actions_list = ["publish_all_drafts"]
    actions_detail = ["open_comments"]
    actions_submit_line = ["save_publish"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Optimize post queryset."""

        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related(
                "tags",
                "comment_set__author",
            )
            .annotate(
                comments_total=Count("comment", distinct=True)
            )
        )

    @display(description="Post", header=True)
    def post_header(self, obj: Post) -> tuple:
        """Return post title and author."""

        return (
            obj.title,
            obj.author.email,
        )

    @display(
        description="Status",
        ordering="status",
        label={
            Post.StatusType.PUBLISHED: "success",
            Post.StatusType.DRAFT: "warning",
        },
    )
    def status_label(self, obj: Post) -> tuple:
        """Return colored post status."""

        return (
            obj.status,
            obj.get_status_display(),
        )

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict:
        """Return tags as dropdown items."""

        tags: list[Tag] = list(obj.tags.all())

        return {
            "title": f"{len(tags)} tags",
            "items": (
                [
                    {"title": tag.name}
                    for tag in tags
                ]
                if tags
                else [{"title": "No tags"}]
            ),
        }

    @display(
        description="Comments",
        ordering="comments_total",
    )
    def comments_count(self, obj: Post) -> int:
        """Return number of comments."""

        return obj.comments_total

    @admin.action(description="Publish selected")
    def publish_selected(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> None:
        """Publish selected posts."""

        updated: int = queryset.update(
            status=Post.StatusType.PUBLISHED,
            updated_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} posts published.",
        )

    @admin.action(description="Move to drafts")
    def move_to_drafts(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> None:
        """Move selected posts to drafts."""

        updated: int = queryset.update(
            status=Post.StatusType.DRAFT,
            updated_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} posts moved to drafts.",
        )

    @action(
        description="Publish / unpublish",
        url_path="toggle-status",
        permissions=["blog.change_post"],
    )
    def toggle_status(
        self,
        request: HttpRequest,
        object_id: str,
    ):
        """Toggle publication status of one post."""

        post: Post = get_object_or_404(
            Post,
            pk=object_id,
        )

        if post.status == Post.StatusType.PUBLISHED:
            post.status = Post.StatusType.DRAFT
        else:
            post.status = Post.StatusType.PUBLISHED

        post.save(
            update_fields=("status", "updated_at")
        )

        self.message_user(
            request,
            "Post status updated.",
        )

        return redirect("admin:blog_post_changelist")

    @action(
        description="Publish all drafts",
        url_path="publish-all-drafts",
        permissions=["blog.change_post"],
    )
    def publish_all_drafts(self, request: HttpRequest):
        """Publish all draft posts."""

        updated: int = Post.objects.filter(
            status=Post.StatusType.DRAFT,
        ).update(
            status=Post.StatusType.PUBLISHED,
            updated_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} drafts published.",
        )

        return redirect("admin:blog_post_changelist")

    @action(
        description="Open comments",
        url_path="comments",
        permissions=["blog.view_comment"],
    )
    def open_comments(
        self,
        request: HttpRequest,
        object_id: str,
    ):
        """Open comments filtered by the current post."""

        url: str = reverse(
            "admin:blog_comment_changelist"
        )

        return redirect(
            f"{url}?post__id__exact={object_id}"
        )

    @action(
        description="Save & publish",
        permissions=["blog.change_post"],
    )
    def save_publish(
        self,
        request: HttpRequest,
        obj: Post,
    ) -> None:
        """Publish a post after saving its form."""

        Post.objects.filter(pk=obj.pk).update(
            status=Post.StatusType.PUBLISHED,
            updated_at=timezone.now(),
        )

        self.message_user(
            request,
            "Post saved and published.",
        )
