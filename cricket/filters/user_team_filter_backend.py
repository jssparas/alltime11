from rest_framework import filters


class UserTeamFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        match_id = request.query_params.get("match_id")
        if match_id:
            queryset = queryset.filter(match__id=match_id)

        return queryset
