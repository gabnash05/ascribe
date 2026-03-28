from celery import Celery

from app.workers.celery_app import celery_app


def test_celery_app_is_celery_instance():
    assert isinstance(celery_app, Celery)


def test_app_name():
    assert celery_app.main == "ascribe"


def test_task_serializer_is_json():
    assert celery_app.conf.task_serializer == "json"


def test_accept_content_includes_json():
    assert "json" in celery_app.conf.accept_content


def test_result_serializer_is_json():
    assert celery_app.conf.result_serializer == "json"


def test_prefetch_multiplier_is_one():
    # Ensures each worker only picks up one task at a time —
    # critical for memory-heavy ingestion jobs.
    assert celery_app.conf.worker_prefetch_multiplier == 1


def test_acks_late_is_enabled():
    # Task must only be acknowledged AFTER completion, not on pickup.
    assert celery_app.conf.task_acks_late is True


def test_ingestion_module_in_includes():
    assert "app.workers.ingestion" in celery_app.conf.include
