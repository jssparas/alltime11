from .settings import *  # Import all default settings

# Testing-specific settings
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
