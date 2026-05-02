from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from allauth.account.views import LoginView, SignupView, LogoutView
from .forms import CustomSignupForm
from core.models import InterestRegistration
from seasons.models import Season
from teams.models import Team
from fixtures.models import Match
from standings.models import Standing


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


class CustomSignupView(SignupView):
    template_name = "accounts/signup.html"
    form_class = CustomSignupForm


class CustomLogoutView(LogoutView):
    template_name = "accounts/logout.html"


# Create your views here.
@login_required
def admin_dashboard_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    context = {
        "pending_interest_count": InterestRegistration.objects.filter(status="pending").count(),
        "pending_team_count": Team.objects.filter(status="pending").count(),
        "active_seasons": Season.objects.filter(status="active").order_by("name"),
        "total_teams": Team.objects.filter(status="approved").count(),
    }
    return render(request, "accounts/admin_dashboard.html", context)


@login_required
def captain_dashboard_view(request):
    if request.user.role not in ("captain", "vice_captain"):
        raise PermissionDenied
    team = (
        Team.objects.filter(captain=request.user).first()
        or Team.objects.filter(vice_captain=request.user).first()
    )
    if not team:
        return redirect("home")
    matches = (
        Match.objects.filter(season=team.season)
        .filter(models.Q(team_a=team) | models.Q(team_b=team))
        .order_by("round_number", "date", "time")
        .select_related("team_a", "team_b")
    )
    next_fixture = (
        Match.objects.filter(season=team.season)
        .filter(models.Q(team_a=team) | models.Q(team_b=team))
        .filter(status="scheduled")
        .order_by("date", "time")
        .select_related("team_a", "team_b")
        .first()
    )
    all_standings = list(
        Standing.objects.filter(season=team.season)
        .order_by("-points", "-wins")
        .select_related("team")
    )
    standings_rows = [{"position": i + 1, "standing": s} for i, s in enumerate(all_standings)]
    league_position = None
    league_points = None
    for row in standings_rows:
        if row["standing"].team == team:
            league_position = row["position"]
            league_points = row["standing"].points
            break

    return render(request, "accounts/captain_dashboard.html", {
        "team": team,
        "season": team.season,
        "matches": matches,
        "next_fixture": next_fixture,
        "standings_rows": standings_rows,
        "league_position": league_position,
        "league_points": league_points,
        "total_teams": len(all_standings),
    })
