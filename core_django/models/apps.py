"""
Django app configuration for Weather Data Engineering API models.
"""

from django.apps import AppConfig


class ModelsConfig(AppConfig):
    """
    Django app configuration for the models package.

    This app contains all Django ORM models for the Weather Data Engineering API.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core_django.models"
    verbose_name = "Weather Data Models"
