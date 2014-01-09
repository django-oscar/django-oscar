# -*- coding: utf-8 -*-

# Code will only work with Django >= 1.5. See tests/config.py

from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=CustomUserManager.normalize_email(email),
            username=username,
            is_active=True,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        u = self.create_user(username, email, password=password)
        u.is_admin = True
        u.is_staff = True
        u.save(using=self._db)
        return u


class User(AbstractUser):
    objects = CustomUserManager()
