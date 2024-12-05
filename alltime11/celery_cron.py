from celery.schedules import crontab


# BEAT SCHEDULER;;
beat_tasks = {
    'save-featured-tournaments-cron': {
        'task': 'cricket.tasks.save_featured_tournaments_cron',
        'schedule': crontab(hour='22', minute='30', day_of_week='*')
    },
    'fetch-match-list-cron': {
        'task': 'cricket.tasks.fetch_match_list_cron',
        'schedule': crontab(hour='23', minute='30', day_of_week='*')
    },
    # 'update-not-started-match-with-title-cron': {
    #     'task': 'cricket.tasks.update_not_started_match_cron',
    #     'schedule': crontab(hour='01', minute='30', day_of_week='*'),
    #     'kwargs': {'title_check': True}
    # },
    'task-schedule-match-lineups-status-update': {
        'task': 'cricket.tasks.task_schedule_match_lineups_status_update',
        'schedule': crontab(hour='0', minute='30', day_of_week='*')
    },
    'schedule-contest_start-job-cron': {
        'task': 'cricket.tasks.task_schedule_contest_start_jobs',
        'schedule': crontab(hour='0', minute='30', day_of_week='*'),
    },
    'update-livematch-score-cron': {
        'task': 'cricket.tasks.update_not_started_match_cron',
        'schedule': crontab(minute='*/30'),
        'kwargs': {'status': "started"}
    },
    'update-player-match-points': {
        'task': 'cricket.tasks.task_update_player_points_cron',
        'schedule': crontab(minute='*/5')
    }
    # 'update-match-tbc-team': {
    #     'task': 'cricket.tasks.task_update_match_tbc_team',
    #     'schedule': crontab(hour='9', minute='30', day_of_week='*')
    # }
}