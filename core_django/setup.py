"""
Django setup utility for FastAPI integration.

This module provides utilities to initialize Django ORM within FastAPI applications,
allowing the use of Django models without running the full Django web framework.
"""

import os
import django
from django.conf import settings


def setup_django() -> None:
    """
    Initialize Django for use with FastAPI.
    
    This function configures Django settings and sets up the ORM
    for use in FastAPI applications.
    
    Call this function before importing Django models in FastAPI code.
    """
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")
        django.setup()


def ensure_django_setup(func):
    """
    Decorator to ensure Django is set up before calling a function.
    
    This decorator automatically calls setup_django() if Django
    hasn't been configured yet.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    def wrapper(*args, **kwargs):
        setup_django()
        return func(*args, **kwargs)
    
    return wrapper 