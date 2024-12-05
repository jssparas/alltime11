"""users URL Configuration
"""
from django.urls import path
from .views import MatchListView, MatchRetrieveView, ContestListCreateView, ContestRetrieveUpdateView,\
    UserTeamListCreateView, UserTeamRetrieveUpdateView, UserTeamContestListCreate, MyContestListView,\
    MatchPlayerRetrieveView, TeamListView, TeamRetrieveView, TournamentListView, TournamentRetrieveView, \
    MatchScoreCardView, MatchGuideView, UserTeamPlayerStatusView

urlpatterns = [
    path('matches', MatchListView.as_view()),
    path('match/<int:pk>', MatchRetrieveView.as_view()),
    path('match/<int:match_id>/contests', ContestListCreateView.as_view()),
    path('match/<int:match_id>/mycontests', MyContestListView.as_view(), name='mycontests'),
    path('contest/<int:pk>', ContestRetrieveUpdateView.as_view()),
    path('match/<int:match_id>/userteams', UserTeamListCreateView.as_view()),
    path('userteam/<int:pk>', UserTeamRetrieveUpdateView.as_view()),
    path('userteamcontests', UserTeamContestListCreate.as_view()),
    path('matchplayer/<int:pk>', MatchPlayerRetrieveView.as_view()),
    path('tournaments', TournamentListView.as_view()),
    path('tournament/<int:pk>', TournamentRetrieveView.as_view()),
    path('teams', TeamListView.as_view()),
    path('team/<int:pk>', TeamRetrieveView.as_view()),
    path('match/<int:pk>/scorecard', MatchScoreCardView.as_view()),
    path('match/<int:pk>/guide', MatchGuideView.as_view()),
    path('match/<int:match_id>/userteam/<int:pk>/playerstatus', UserTeamPlayerStatusView.as_view()),
]
