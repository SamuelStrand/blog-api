from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class CustomUserManager(BaseUserManager):
    """
    Custom User Manager for Custom User
    """
    def __obtain_user_instance(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str,
            **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """
        Get user instance
        """
        if not email:
            raise ValidationError(
                message="Email is required"
            )
        if not first_name and last_name:
            raise ValidationError(
                message="First name and last name are required"
            )

        new_user: 'CustomUser' = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            password=password,
            **kwargs,
        )

        return new_user

    def create_user(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str,
            **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """
        Creates Custom User
        """
        new_user: 'CustomUser' = self.__obtain_user_instance(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        **kwargs: dict[str, Any],
    ) -> 'CustomUser':
        """
        Creates Super User
        """
        new_user: 'CustomUser' = self.__obtain_user_instance(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_staff=True,
            is_superuser=True,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model extending AbstractBaseUser and PermissionsMixin
    """

    EMAIL_MAX_LENGTH = 150
    FULL_NAME_MAX_LENGTH = 50

    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        db_index=True
    )
    first_name = models.CharField(
        max_length=FULL_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        max_length=FULL_NAME_MAX_LENGTH
    )
    is_active = models.BooleanField(
        default=True
    )
    is_staff = models.BooleanField(
        default=False
    )

    REQUIRED_FIELDS = ["first_name", "last_name"]
    USERNAME_FIELD = "email"
    objects = CustomUserManager()
