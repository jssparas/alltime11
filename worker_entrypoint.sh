# run a worker :)
celery -A alltime11 worker --loglevel=debug --concurrency 4 -E