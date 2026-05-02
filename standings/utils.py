from django.db import models
from fixtures.models import Match
from teams.models import Team
from .models import Standing


def update_standings(season):
    teams = Team.objects.filter(season=season, status="approved")

    rows = []
    for team in teams:
        played_matches = Match.objects.filter(season=season, status="played").filter(
            models.Q(team_a=team) | models.Q(team_b=team)
        )

        played = played_matches.count()
        wins = losses = draws = 0

        for match in played_matches:
            if match.team_a == team:
                my_score, their_score = match.team_a_score, match.team_b_score
            else:
                my_score, their_score = match.team_b_score, match.team_a_score

            if my_score > their_score:
                wins += 1
            elif my_score < their_score:
                losses += 1
            else:
                draws += 1

        pts = wins * 4 + draws * 2

        rows.append(
            {
                "team": team,
                "played": played,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "pts": pts,
            }
        )

    # sort by points desc, wins desc
    rows.sort(key=lambda r: (-r["pts"], -r["wins"]))

    # last-place penalty
    if rows and rows[-1]["wins"] == 0 and rows[-1]["played"] > 0:
        rows[-1]["pts"] = -rows[-1]["played"]

    # save to DB
    for row in rows:
        Standing.objects.update_or_create(
            season=season,
            team=row["team"],
            defaults={
                "played": row["played"],
                "wins": row["wins"],
                "losses": row["losses"],
                "draws": row["draws"],
                "points": row["pts"],
            },
        )
