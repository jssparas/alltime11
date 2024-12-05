import logging
from datetime import datetime, timedelta
from decimal import Decimal

from celery import shared_task
from django.db.models import Q, Case, When, Value, IntegerField
from django.utils import timezone
from django.contrib.auth import get_user_model

from alltime11.constants import (
    MATCH_STATUS_NOT_STARTED, MATCH_STATUS_STARTED, PLAYER_ROLE_BOWLER,
    MATCH_STATUS_COMPLETED, PLAYER_ROLE_BATSMAN, PLAYER_ROLE_KEEPER,
    PLAYER_ROLE_ALLROUNDER
)
from alltime11 import constants
from cricket.models import Tournament, Match, Team, Player, MatchPlayer, Contest, UserTeamContest
from service.rounaz.api import *
from service.firebase.api import fcm_send_push_notification
from utils.helpers import chunks

User = get_user_model()
high_logger = logging.getLogger('celery.high')
mid_logger = logging.getLogger('celery.mid')
low_logger = logging.getLogger('celery.low')


@shared_task(queue='mid')
def save_featured_tournaments_cron():
    # fetch tournaments
    try:
        data = get_featured_tournaments()
        if len(data["tournaments"]) > 0:
            for tournament in data.get("tournaments"):
                # fetch only ICC and BCC tournaments for now
                if tournament.get("association_key") and "icc" not in tournament.get("association_key"):
                    mid_logger.info('Tournament Fetch Cron, Tournament is not ICC type, key: %s', tournament.get("key"))
                    continue
                last_scheduled_match_date = start_date = None
                if tournament.get("start_date"):
                    start_date = datetime.fromtimestamp(tournament.get("start_date"))
                #print("start_date", start_date)
                if tournament.get("last_scheduled_match_date"):
                    last_scheduled_match_date = datetime.fromtimestamp(tournament.get("last_scheduled_match_date"))

                # check tournament exist or not
                if Tournament.objects.filter(uid=tournament.get("key")).exists():
                    mid_logger.info('Tournament Fetch Cron, Tournament already exist, key: %s', tournament.get("key"))
                    # if tournament found then update it
                    Tournament.objects.filter(uid=tournament.get("key")).update(
                            name=tournament.get("name"),
                            short_name=tournament.get("short_name"),
                            association_id=tournament.get("association_key"),
                            gender=tournament.get("gender"),
                            is_date_confirmed=tournament.get("is_date_confirmed"),
                            is_venue_confirmed=tournament.get("is_venue_confirmed"),
                            start_date=start_date,
                            last_scheduled_match_date=last_scheduled_match_date,
                            country=tournament['countries'][0]['short_code'] if len(tournament['countries']) > 0 else None,
                        )
                    continue
                # Now insert
                tt_obj = Tournament(
                            uid=tournament.get("key"),
                            name=tournament.get("name"),
                            short_name=tournament.get("short_name"),
                            association_id=tournament.get("association_key"),
                            gender=tournament.get("gender"),
                            is_date_confirmed=tournament.get("is_date_confirmed"),
                            is_venue_confirmed=tournament.get("is_venue_confirmed"),
                            start_date=start_date,
                            last_scheduled_match_date=last_scheduled_match_date,
                            country=tournament['countries'][0]['short_code'] if len(tournament['countries']) > 0 else None,
                        )
                try:
                    tt_obj.save()
                except Exception as ex:
                    mid_logger.error('Tournament Fetch Cron, Error while saving Tournament, key: %s, Error: %s', tournament.get("key"), ex)
    except Exception as ex:
        mid_logger.error("Tournaments fetch cron Error: %s", ex)


def save_featured_matches(tournament_key=None, page_key=None):
    if tournament_key:
        data = get_tournament_fixtures(tournament_key, page_key)
        mid_logger.error("Match Fetch List Cron, match data fetched for tournament %s, No of matches %s", \
                    tournament_key, len(data["matches"]))
    else:
        data = get_featured_matches()
    # print("Match data ----------", data)
    if len(data["matches"]) > 0:
        for match in data["matches"]:
            if match.get("status") != MATCH_STATUS_NOT_STARTED:
                mid_logger.info('Match Fetch List Cron,Match is not in not started status, key: %s', match.get("key"))
                continue
            # if match venue not decided then empty venue details we get
            if not match["venue"].get("key", None):
                mid_logger.info('Match Fetch List Cron,Match venue is not decided yet, key: %s', match.get("key"))
                continue
            # check team decided or not
            teams = match.get("teams")
            if not teams.get("a").get("key", None) or teams.get("a") == "tbc" or \
                not teams.get("b").get("key", None) or teams.get("b") == "tbc":
                mid_logger.info('Match Fetch List Cron,Match teams not decided yet, key: %s', match.get("key"))
                continue
            start_date = ""
            if match.get("start_at"):
                start_date = datetime.fromtimestamp(match.get("start_at"))
                next10_dates = timezone.now().date() + timedelta(days=10)
                if start_date.date() >= next10_dates: # only storing within days matches
                    continue
            # check match exist or not in db
            if Match.objects.filter(uid=match.get("key")).exists():
                mid_logger.info('Match Fetch List Cron,Match already exist, key: %s', match.get("key"))
                continue
            # now call single match detail api and check other data parameters
            match_data = get_match_data(match.get("key"))
            # mid_logger.info('save_featured_matches match_data-----: %s', match_data)
            data_review = match_data.get("data_review")
            mid_logger.info('Match Fetch List Cron, Match data_review-----: %s', data_review)
            if data_review.get("team_a") is False or not check_teams_containing_players(match_data) \
                or  data_review.get("team_b") is False or data_review.get("schedule") is False:
                mid_logger.info('Match Fetch List Cron,Match data review params incomplete, key: %s', match.get("key"))
                continue
            # Team create
            teama_obj, teamb_obj = team_fetch_or_create(match.get("teams"))
            mid_logger.info("Match List Cron,Match Key: %s, Team A: %s, Team B: %s", match.get("key"), teama_obj, teamb_obj)
            # Check Tournament and create if not exist
            tournament_obj = get_match_tournament_id(match.get("tournament"), match["association"].get("key"))

            # insert match
            match_obj = Match(uid=match.get("key"), name=match.get("name"), short_name=match.get("short_name"),
                              subtitle=match.get("sub_title"), status=match.get("status"), start_date=start_date,
                              association_id=match["association"].get("key"), gender=match.get("gender"),
                              venue_name=match["venue"].get("name"), venue_city=match["venue"].get("city"),
                              venue_country=match["venue"]["country"].get("short_code"),
                              tournament=tournament_obj, team_a=teama_obj, team_b=teamb_obj,
                              match_format=match.get("format"))
            try:
                match_obj.save()
                mid_logger.info("Match List cron, Match data saved %s", match_obj)
                # update match data
                update_single_match_info(match.get("key"), match_data=match_data)
                # create dummy contest for now
                if settings.DEBUG:
                    contest_create_script(match_obj.id)
            except Exception as ex:
                mid_logger.error("Error while saving Match, key: %s, Error: %s", match.get("key"), ex)

    # call recursively if we get next page key
    if data.get("next_page_key"):
        save_featured_matches(tournament_key=tournament_key, page_key=data.get("next_page_key"))
    else:
        mid_logger.info("All matches updated for Tournament key: %s", tournament_key)


def check_teams_containing_players(match_data):
    match_squad = match_data.get("squad")
    if len(match_squad) > 0 and match_squad.get('a') and len(match_squad.get('a').get('player_keys')) > 12 \
            and match_squad.get('b') and len(match_squad.get('b').get('player_keys')) > 12:
        return True
    return False


def team_fetch_or_create(teams):
    teama_obj = teamb_obj = None
    if len(teams) > 0:
        for key, team_info in teams.items():
            team_objs = Team.objects.filter(uid=team_info.get("key"))
            if team_objs.exists():
                team_obj = team_objs[0]
                mid_logger.info("Team already exist: %s", team_obj)
            else:
                # insert into Team
                team_obj = Team(
                                uid=team_info.get("key"),
                                name=team_info.get("name")
                            )
                try:
                    team_obj.save()
                    mid_logger.info("New Team saved: %s", team_obj)
                except Exception as ex:
                    mid_logger.error("Error while saving Team, key: %s, Error: %s", team_info.get("key"), ex)
            if key == "a":
                teama_obj = team_obj
            elif key == "b":
                teamb_obj = team_obj
    return teama_obj, teamb_obj


def get_match_tournament_id(tournament, association_key=None):
    tournament_obj = None
    try:
        tournament_obj = Tournament.objects.get(uid=tournament.get("key", None))
    except Tournament.DoesNotExist:
        # create Tournament
        tournament_obj = Tournament(
                uid=tournament.get("key"),
                name=tournament.get("name"),
                short_name=tournament.get("short_name"),
                association_id=association_key
            )
        try:
            tournament_obj.save()
        except Exception as ex:
            mid_logger.error("Error while saving Tournament, key: %s, Error: %s", tournament.get("key"), ex)
    return tournament_obj


def update_single_match_info(match_key, is_tbc_team_update=False, match_data=None):
    # check match exist
    try:
        match = Match.objects.get(uid=match_key)
    except Match.DoesNotExist:
        mid_logger.info("Match Not exist into DB, can't fetch data")
        raise
    if not match_data:
        match_data = get_match_data(match_key)
    mid_logger.info("update_single_match_info match_data--- %s", match_data)
    #if match_data.get("status") == MATCH_STATUS_NOT_STARTED:
    match.title = match_data.get("title")
    match.play_status = match_data.get("play_status")
    match.status = match_data.get("status")
    match.name = match_data.get("name")
    match.short_name = match_data.get("short_name")

    if match_data.get("start_at"):
        match.delayed_time = datetime.fromtimestamp(match_data.get("start_at"))
    teama_obj = teamb_obj = None
    if len(match_data.get("players")) > 0:
        teama_obj, teamb_obj = team_fetch_or_create(match_data.get("teams"))
        if is_tbc_team_update:
            match.team_a = teama_obj
            match.team_b = teamb_obj
        player_credits = fetch_player_credits(match_key) if match_data.get("status") == MATCH_STATUS_NOT_STARTED and \
                            not MatchPlayer.is_player_credits_updated(match.id) else None
        mid_logger.info("update_single_match_info player_credits--- %s", player_credits)
        player_points =  fetch_player_points(match_key) if (match_data.get("status") == MATCH_STATUS_NOT_STARTED \
                            and not MatchPlayer.is_player_tournament_points_updated(match.id)) \
                            or match_data.get("status") == MATCH_STATUS_COMPLETED else None
        mid_logger.info("update_single_match_info player_points--- %s", player_points)
        credit_points = {
                       "player_points": player_points,
                       "player_credits": player_credits
                    }
        mid_logger.info("update_single_match_info team A squad--- %s", match_data["squad"]["a"])
        # insert team A players
        insert_team_players(match, teama_obj, match_data["squad"]["a"], match_data["players"], **credit_points)
        # insert team B players
        mid_logger.info("update_single_match_info team B squad--- %s", match_data["squad"]["b"])
        insert_team_players(match, teamb_obj, match_data["squad"]["b"], match_data["players"], **credit_points)

    if not match.toss_info:
        match.toss_info = match_data.get("toss", None)
    if match_data.get("play", None):
        play_info = match_data.get("play")
        if not match.first_batting:
            if match_data["teams"][play_info.get("first_batting")]["key"] == teama_obj.uid:
                match.first_batting = teama_obj
            elif match_data["teams"][play_info.get("first_batting")]["key"] == teamb_obj.uid:
                match.first_batting = teamb_obj
            else:
                mid_logger.info("Error Invalid Team")
        match.target_info = play_info.get("target", None)
        if play_info.get("result", None):
            result_data = play_info.get("result")
            match.win_type = result_data.get("result_type", None)
            match.win_message = result_data.get("msg", None)
            if result_data.get("winner"):
                if match_data["teams"][result_data.get("winner")]["key"] == teama_obj.uid:
                    match.winner = teama_obj
                elif match_data["teams"][result_data.get("winner")]["key"] == teamb_obj.uid:
                    match.winner = teamb_obj
            if len(result_data.get("pom")) > 0:
                player_obj = Player.objects.filter(uid=result_data.get("pom")[0]).first()
                match.pom = player_obj
        #if match_data.get("status") == MATCH_STATUS_COMPLETED and match_data.get("play_status") == "result":
        team_a_data = play_info["innings"].get("a_1")
        team_a_score = {
                        "score_str": team_a_data["score_str"],
                        "score": team_a_data["score"],
                        "wickets": team_a_data["wickets"],
                        "extra_runs": team_a_data["extra_runs"],
                        "balls_breakup": team_a_data["balls_breakup"]
                    }
        team_b_data = play_info["innings"].get("b_1")
        team_b_score = {
                        "score_str": team_b_data["score_str"],
                        "score": team_b_data["score"],
                        "wickets": team_b_data["wickets"],
                        "extra_runs": team_b_data["extra_runs"],
                        "balls_breakup": team_b_data["balls_breakup"]
                    }

        match.team_a_score = team_a_score
        match.team_b_score = team_b_score
    match.save()

    # TODO: discuss what happens if contest wasn't filled
    if match.status == constants.MATCH_STATUS_COMPLETED:
        Contest.objects.filter(match=match).update(status=constants.CONTEST_STATUS_COMPLETED)


def insert_team_players(match_obj, team_obj, team_squad, players_info, **kwargs): # Team A and Team B
    player_keys = team_squad.get("player_keys")
    captain_key = team_squad["captain"]
    player_credits = kwargs.get("player_credits")
    player_points = kwargs.get("player_points")
    is_playing_update = True if len(team_squad["playing_xi"]) > 0 else False

    for player_key in player_keys:
        # get player info
        player_data = players_info[player_key]
        player_obj = insert_player(player_key, player_data)
        if player_obj:
            # match player exist or not
            match_player = MatchPlayer.objects.filter(
                                match_id=match_obj.id,
                                team_id=team_obj.id,
                                player_id=player_obj.id
                            )
            if not match_player.exists():
                match_player_obj = MatchPlayer(
                                    match=match_obj,
                                    team=team_obj,
                                    player=player_obj,
                                    is_captain=True if captain_key == player_key else False,
                                    is_keeper=True if player_obj.seasonal_role == PLAYER_ROLE_KEEPER else False,
                                    is_batsman=True if player_obj.seasonal_role == PLAYER_ROLE_BATSMAN or \
                                                    player_obj.seasonal_role == PLAYER_ROLE_KEEPER else False,
                                    is_bowler=True if player_obj.seasonal_role == PLAYER_ROLE_BOWLER else False,
                                    is_all_rounder=True if player_obj.seasonal_role == PLAYER_ROLE_ALLROUNDER else False,
                                    roles=[player_obj.seasonal_role],
                                    playing_order=1
                                )
                try:
                    match_player_obj.save()
                    mid_logger.info("Match Player saved %s", match_player_obj)
                except Exception as ex:
                    mid_logger.error("Error while saving match player, key: %s, Error: %s", player_key, ex)
            else:
                match_player_obj = match_player.first()
            # update player credits and points
            try:
                # update playing xi
                if is_playing_update and player_key in team_squad["playing_xi"]:
                    match_player_obj.is_playing = True
                    match_player_obj.playing_order = team_squad["playing_xi"].index(player_key)+1

                if player_credits and player_key in player_credits:
                    match_player_obj.player_credits = player_credits[player_key]
                if player_points and player_key in player_points:
                    point_data = player_points[player_key]
                    match_player_obj.player_tournament_points = point_data.get("tournament_points")
                    match_player_obj.player_points = point_data.get("points")
                    match_player_obj.player_rank = point_data.get("rank")
                if player_data.get("score") and match_obj.status in {MATCH_STATUS_STARTED, MATCH_STATUS_COMPLETED}:
                    # then update player score
                    player_score = player_data.get("score")["1"]
                    if player_score.get("batting"):
                        match_player_obj.batting_stats = player_score['batting']['score']
                    if player_score.get("bowling"):
                        match_player_obj.bowling_stats = player_score['bowling']['score']
                match_player_obj.save()
            except Exception as ex:
                mid_logger.error("Error while saving match player credits or points, key: %s, Error: %s", player_key, ex)


def insert_player(player_key, player_data):
    # check player key exist
    pinfo = player_data.get("player")
    player_obj = None
    try:
        player_obj = Player.objects.get(uid=player_key)
    except Player.DoesNotExist:
        bowling_style = None
        if pinfo.get("bowling_style", None):
            bowling_style = pinfo["bowling_style"]["arm"]
        try:
            player_obj = Player(
                        uid=player_key,
                        name=pinfo.get("name"),
                        gender='M' if pinfo.get("gender") == "male" else 'F',
                        nationality=pinfo["nationality"].get("short_code", None)\
                            if pinfo["nationality"] else None,
                        date_of_birth=datetime.fromtimestamp(pinfo.get("date_of_birth")).date() if pinfo.get("date_of_birth", None) else None,
                        seasonal_role=pinfo.get("seasonal_role", None),
                        batting_style=pinfo.get("batting_style", None),
                        bowling_style=bowling_style,
                        skills=pinfo.get("skills", None),
                        jersey_name=pinfo.get("jersey_name"),
                        legal_name=pinfo.get("legal_name")
                    )
        
            player_obj.save()
            mid_logger.info("Player saved %s", player_obj)
        except Exception as ex:
            mid_logger.error("Error while saving player info, key: %s, Error: %s", player_key, ex)
    return player_obj


def fetch_player_credits(match_key):
    credits = {}
    credits_data = get_match_player_credits(match_key).get("credits", [])
    # mid_logger.info("credits_data------------- %s", credits_data)
    for credit in credits_data:
        credits[credit.get("player_key")] = credit.get("value")
    return credits


@shared_task(queue='mid')
def update_not_started_match_cron(status=MATCH_STATUS_NOT_STARTED, title_check=False):
    # fetch all not started matches
    try:
        matches = Match.objects.filter(status=status)
        if title_check:
            matches = matches.filter(title__isnull=True)
        if matches.count() == 0:
            mid_logger.info("No match found for update with status not started or started")
            return
        for match in matches:
            try:
                mid_logger.info("update_not_started_match_cron task, Match: %s", match)
                update_single_match_info(match.uid)
            except Exception as ex:
                mid_logger.error("Error to update match, key: %s and error: %s", match.uid, ex)
    except Exception as ex:
        mid_logger.error("Error in updating not started match cron, Error: %s", ex)


@shared_task(queue='high')
def match_status_update_tobe_started_task(match_uid):
    try:
        update_single_match_info(match_uid)
        # send push notification if match started
        match = Match.objects.filter(uid=match_uid).values('toss_info', 'uid', 'status', 'play_status', 'id').first()
        if match.get('status') == MATCH_STATUS_NOT_STARTED and match.get('toss_info'):
            # find next schedule time on the basis of current time
            scheduled_time = timezone.now() + timedelta(minutes=10)
            high_logger.info("Match task scheduled, match_id: %s", match.get('uid'))
            match_status_update_tobe_started_task.apply_async(args=(match.get('uid'), ), eta=scheduled_time)

        if match.get('play_status') == "in_play":
            send_match_started_notifications_batch.delay(match.get("id"))
        else:
            high_logger.info(f"Match is not started: {match_uid}")
    except Exception as ex:
        high_logger.error("Error in update match status as started task, \
                key: %s and error: %s", match_uid, ex)


@shared_task(queue='high')
def match_lineups_update_task(match_uid):
    try:
        update_single_match_info(match_uid)
        match = Match.objects.filter(uid=match_uid).values('toss_info', 'uid', 'status', 'id').first()
        if match.get('status') == MATCH_STATUS_NOT_STARTED and not match.get('toss_info'):
            # find next schedule time on the basis of current time
            scheduled_time = timezone.now() + timedelta(minutes=10)
            high_logger.info("Rescheduled lineups task as no toss info updated in previous call")
            match_lineups_update_task.apply_async(args=(match.get('uid'), ), eta=scheduled_time)
        elif match.get('status') == MATCH_STATUS_NOT_STARTED and match.get('toss_info'):
            # calling job to update match status as started
            scheduled_time = timezone.now() + timedelta(minutes=15)
            match_status_update_tobe_started_task.apply_async(args=(match.get('uid'), ), eta=scheduled_time)
            # send push notification if lineups updated
            send_match_linups_out_notifications_batch.delay(match.get("id"))
    except Exception as ex:
        high_logger.error("Error in update match lineups, key: %s and error: %s", match_uid, ex)


@shared_task(queue='high')
def task_schedule_match_lineups_status_update():
    """
    cron task to schedule a task that will trigger before half an hour ago
    and after one minute at match start time
    it will update all the matches lineups and match status to be started
    """
    # TODO: add loggers
    today = timezone.now().date()
    matches = Match.objects.filter(start_date__date=today, status=MATCH_STATUS_NOT_STARTED).values('uid', 'start_date')
    if matches.count() == 0:
        high_logger.info("Cron: task_schedule_match_lineups_update: No match found for scheduling")
        return
    for match in matches:
        # for linups update
        scheduled_time = match.get('start_date') - timedelta(minutes=30)
        high_logger.info("Match lineups task scheduled, Match Id %s", match.get('uid'))
        match_lineups_update_task.apply_async(args=(match.get('uid'), ), eta=scheduled_time)


@shared_task(queue='mid')
def fetch_match_list_cron():
    # fetch all tournaments from db
    try:
        current_date = datetime.now().date()
        tournaments = Tournament.objects.filter(Q(start_date__gte=current_date) | Q(last_scheduled_match_date__gte=current_date))
        if tournaments.count() == 0:
            mid_logger.info("No Tournaments found to fetch matches")
            return
        for tournament in tournaments:
            tournament_key = tournament.uid
            mid_logger.info("tournament_key: %s", tournament_key)
            try:
                save_featured_matches(tournament_key=tournament_key, page_key=1)
            except Exception as ex:
                mid_logger.error("Error in fetching match for tournament, key: %s, Error: %s", tournament_key, ex)
    except Exception as ex:
        mid_logger.error("Error in fetching match list cron, Error: %s", ex)


@shared_task(queue='mid')
def task_schedule_contest_start_jobs():
    """
    cron task to schedule a task that will trigger at match start time
    it will set all the contests status to started for that particular match
    """
    # TODO: add loggers
    today = timezone.now().date()
    matches = Match.objects.filter(start_date__date=today).values('id', 'start_date')
    for match in matches:
        scheduled_time = match.get('start_date') - timedelta(minutes=5)
        task_start_contests.apply_async(args=(match.get('id'), ), eta=scheduled_time)


@shared_task(queue='mid')
def task_start_contests(match_id):
    """
    """
    # TODO: add loggers
    contests = Contest.objects.filter(match__id=match_id, is_active=True, status=constants.CONTEST_STATUS_NOT_STARTED)
    for contest in contests:
        if contest.entries_left == 0:
            contest.status = constants.CONTEST_STATUS_STARTED
            contest.save()
            mid_logger.info("contest started %s", contest)


@shared_task(queue='low')
def task_update_player_points_cron():
    match_ids = Match.objects.filter(status=constants.MATCH_STATUS_STARTED, play_status='in_play').\
        values_list('id', flat=True)
    # match_ids = [126, 130]
    for match_id in match_ids:
        low_logger.info(f"running task_update_player_points task for match {match_id}")
        task_update_player_points.delay(match_id)


@shared_task(queue='mid')
def task_update_player_points(match_id):
    """
    """
    match_key = Match.objects.filter(id=match_id).values("uid")[0].get("uid")
    players = MatchPlayer.objects.filter(match__id=match_id, is_playing=True)
    player_key_wise_points = fetch_player_points(match_key)
    mid_logger.info(f"player key wise points: {player_key_wise_points}")
    for player in players:
        player.player_points = player_key_wise_points.get(player.player.uid).get("points")
        player.save()

    mid_logger.info(f"running task_update_contest_rankings for match {match_id}")
    task_update_contest_rankings.delay(match_id)


@shared_task(queue='high')
def task_update_contest_rankings(match_id):
    contest_ids = Contest.objects.filter(match__id=match_id, is_active=True,
                                         status=constants.CONTEST_STATUS_STARTED).values_list("id", flat=True)
    for con_id in contest_ids:
        high_logger.info(f"updating ranking of user teams in contest: {con_id}")
        utc_query = UserTeamContest.objects.filter(contest__id=con_id).select_related('user_team')
        user_teams = list(map(lambda utc: utc.user_team, utc_query))
        user_teams = sorted(user_teams, key=lambda ut: ut.points, reverse=True)
        when_args = [When(user_team=ut.id, then=Value(idx)) for idx, ut in enumerate(user_teams, start=1)]
        UserTeamContest.objects.filter(contest__id=con_id).update(rank=Case(*when_args, output_field=IntegerField()))
        high_logger.info(f"updated user team ranks in contest {con_id}")
        high_logger.info(f"{task_update_contest_rankings.request.delivery_info}")


@shared_task(queue='low')
def task_update_match_tbc_team():
    match_uids = Match.objects.filter(Q(status=MATCH_STATUS_NOT_STARTED),
                                      Q(Q(team_a__uid__iexact='tbc') | Q(team_b__uid__iexact='tbc')))\
        .values_list('uid', flat=True)
    if match_uids.count() == 0:
        low_logger.info("No match found for update tbc team")
    for match_uid in match_uids:
        try:
            low_logger.info("updating tbc team for match key: ", match_uid)
            update_single_match_info(match_uid, is_tbc_team_update=True)
        except Exception as ex:
            low_logger.error(f"Error in updating match team key {match_uid}, Error: {ex}")


def contest_create_script(match_id):
    from cricket.serializers import ContestSerializer

    contest_data = {
        "name": f"match {match_id} contest 1",
        "entry_fees": 2500,
        "no_of_teams": 10,
        "contest_type": "mega",
        "is_active": True,
        "is_private": False,
        "match_id": match_id,
        "prize_distribution": {
            "5000": "1",
            "4000": "2",
            "3000": "3-5"
        }
    }
    contest_serializer = ContestSerializer(data=contest_data)
    user = get_user_model().objects.get(id=1)
    try:
        if contest_serializer.is_valid(raise_exception=True):
            contest_serializer.save(created_by=user)
    except Exception as ex:
        print(f"Could not create contest for match id: {match_id} and error: {ex}")


def update_player_credit_and_points(match_id):
    """
    """
    # TODO: add loggers
    match_key = Match.objects.filter(id=match_id).values("uid")[0].get("uid")
    players = MatchPlayer.objects.filter(match__id=match_id)
    player_key_wise_points = fetch_player_points(match_key)
    player_key_wise_credits = fetch_player_credits(match_key)

    for player in players:
        player.player_tournament_points = player_key_wise_points.get(player.player.uid).get("tournament_points")
        player.player_rank = player_key_wise_points.get(player.player.uid).get("player_rank")
        player.player_points = player_key_wise_points.get(player.player.uid).get("points")
        player.player_credits = player_key_wise_credits.get(player.player.uid)
        player.save()


@shared_task(queue='high')
def create_head_to_head_contest(data):
    match = Match.objects.get(pk=data.get('match_id'))
    user = User.objects.get(id=data.get("user_id"))
    entry_fees = data.get("entry_fees")
    prize = 2 * Decimal(entry_fees)
    prize_distribution = {str(prize - (prize * Decimal(str(constants.PLATFORM_FEES)))): "1"}
    contest = Contest.objects.create(match=match, tournament=match.tournament, contest_type='head_to_head',
                                     name=data.get("name"), entry_fees=entry_fees, created_by=user, is_active=True,
                                     no_of_teams=2, prize=prize, prize_distribution=prize_distribution)
    contest.save()


@shared_task(queue='mid')
def send_match_linups_out_notifications_batch(match_id=None):
    try:
        users = User.objects.filter(is_active=True, firebase_token__isnull=False)\
                    .exclude(firebase_token='').values("id", "firebase_token")
        if len(users) == 0:
            mid_logger.info("No users found for sending match lineups out push notification")
        for user_data in chunks(users, 10):
            send_match_linups_out_notification_subtask.delay(match_id, user_data)
    except Exception as ex:
        mid_logger.error("Could not send match lineups out notification for match: \
            %s, error: %s", match_id, ex)


@shared_task(queue='mid')
def send_match_linups_out_notification_subtask(match_id=None, users=[]):
    try:
        match_data = Match.objects.values("name").get(id=match_id)
        for user in users:
            notification_data = {
                                    "firebase_user_token": user.get("firebase_token"),
                                    "msg_title": f"Line Ups Out {match_data.get('name')}",
                                    "msg_body": "Plz create team and join contest"
                                }
            try:
                status, error = fcm_send_push_notification(**notification_data)
                if status:
                    mid_logger.info("Line ups out Notification sent successfully to user: %s \
                        for match: %s ", user.get('id'), match_id)
                else:
                    mid_logger.info("Line ups out Notification could not sent to user: %s for match: %s \
                        and Error: %s", user.get('id'), match_id, error)
            except Exception as ex:
                mid_logger.error("Line ups out Notification could not sent to user: %s for match: %s \
                        and Error: %s", user.get('id'), match_id, ex)
    except Exception as ex:
        mid_logger.error("Could not send match lineups out notification for match: \
            %s, error: %s", match_id, ex)


@shared_task(queue='mid')
def send_match_started_notifications_batch(match_id=None):
    try:
        users = User.objects.filter(is_active=True, firebase_token__isnull=False)\
                    .exclude(firebase_token='').values("id", "firebase_token")
        if len(users) == 0:
            mid_logger.info("No users found for sending match started push notification")
        for user in chunks(users, 10):
            send_match_linups_out_notification_subtask.delay(match_id, user)
    except Exception as ex:
        mid_logger.error("Could 2not send match started notification for match: \
            %s, error: %s", match_id, ex)


@shared_task(queue='mid')
def send_match_started_notifications_subtask(match_id=None, users=[]):
    try:
        match_data = Match.objects.values("name").get(id=match_id)
        for user in users:
            notification_data = {
                                    "firebase_user_token": user.get("firebase_token"),
                                    "msg_title": f"Match Started {match_data.get('name')}",
                                    "msg_body": "Plz join contest"
                                }

            try:
                status, error = fcm_send_push_notification(**notification_data)
                if status:
                    mid_logger.info("Match started Notification sent successfully to user: %s \
                        for match: %s ", user.get('id'), match_id)
                else:
                    mid_logger.info("Match started Notification could not sent to user: %s for match: %s \
                        and Error: %s", user.get('id'), match_id, error)
            except Exception as ex:
                mid_logger.error("Match started Notification could not sent to user: %s for match: %s \
                        and Error: %s", user.get('id'), match_id, ex)
    except Exception as ex:
        mid_logger.error("Could not send match started notification for match: \
            %s, error: %s", match_id, ex)

