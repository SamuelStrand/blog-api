import os
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from settings.conf import * # noqa


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WSGI_APPLICATION = 'settings.wsgi.application'
ROOT_URLCONF = 'settings.urls'
AUTH_USER_MODEL = "auths.CustomUser"

DJANGO_AND_THIRD_PARTY_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APPS = [
    "apps.blog.apps.BlogConfig",
    "apps.auths.apps.AuthsConfig",
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


UNFOLD = {
    "SITE_TITLE": "Blog API Admin",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content Management System",
    "SITE_SYMBOL": "article",

    "COLORS": {
        "primary": {
            "50": "#f0f9ff",
            "100": "#e0f2fe",
            "200": "#bae6fd",
            "300": "#7dd3fc",
            "400": "#38bdf8",
            "500": "#0ea5e9",
            "600": "#0284c7",
            "700": "#0369a1",
            "800": "#075985",
            "900": "#0c4a6e",
            "950": "#082f49",
        },
    },

    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",

    "SITE_DROPDOWN": [
        {
            "title": "GitHub Repository",
            "icon": "code",
            "link": "https://github.com/SamuelStrand/blog-api",
        },
        {
            "title": "Unfold Documentation",
            "icon": "menu_book",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],

    "COMMAND": {
        "search_models": True,
        "show_history": True,
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy(
                            "admin:blog_post_changelist"
                        ),
                        "badge": "apps.blog.callbacks.drafts_badge",
                        "badge_variant": "warning",
                    },
                    {
                        "title": "Comments",
                        "icon": "comment",
                        "link": reverse_lazy(
                            "admin:blog_comment_changelist"
                        ),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy(
                            "admin:blog_category_changelist"
                        ),
                    },
                    {
                        "title": "Tags",
                        "icon": "sell",
                        "link": reverse_lazy(
                            "admin:blog_tag_changelist"
                        ),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": reverse_lazy(
                            "admin:auths_customuser_changelist"
                        ),
                        "permission": (
                            lambda request: request.user.is_superuser
                        ),
                    },
                    {
                        "title": "Groups",
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy(
                            "admin:auth_group_changelist"
                        ),
                        "permission": (
                            lambda request: request.user.is_superuser
                        ),
                    },
                ],
            },
        ],
    },

    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": reverse_lazy(
                        "admin:blog_post_changelist"
                    ),
                },
                {
                    "title": "Published",
                    "link": lambda request: (
                        reverse("admin:blog_post_changelist")
                        + "?status__exact=published"
                    ),
                },
                {
                    "title": "Drafts",
                    "link": lambda request: (
                        reverse("admin:blog_post_changelist")
                        + "?status__exact=draft"
                    ),
                },
            ],
        },
    ],
}
