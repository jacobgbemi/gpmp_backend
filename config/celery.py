"""
Celery application for GlintPM Private.

No tasks are registered yet in Stage 0 — this wires up the app so
`apps/*/tasks.py` modules are auto-discovered once background jobs
(notifications, PDF report generation, etc.) are introduced.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("glintpm")

# Read CELERY_* settings from Django settings, using the `CELERY_` namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")