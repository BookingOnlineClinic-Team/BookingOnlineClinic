import os
from celery import Celery

from bookingonline import app as flask_app


def make_celery(flask_app):
    celery = Celery(
        flask_app.import_name,
        broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        include=["bookingonline.tasks"],
    )
    celery.conf.update(flask_app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.conf.beat_schedule = {
        "check-pending-refunds-every-1-minutes": {
            "task": "bookingonline.tasks.check_pending_refunds",
            "schedule": 60.0
        },
    }
    return celery


celery = make_celery(flask_app)