from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from allauth.account.views import LoginView, SignupView, LogoutView
from .forms import CustomSignupForm, ProfileForm
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

    from teams.models import Player
    from fixtures.models import PlayerAvailability
    registered_players = Player.objects.filter(team=team, registered=True).select_related("user")

    avail_map = {}
    if next_fixture:
        avail_map = {
            a.player_id: a.status
            for a in PlayerAvailability.objects.filter(match=next_fixture)
        }

    squad_availability = []
    for p in registered_players:
        parts = p.name.strip().split()
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
        gender = p.user.gender if p.user else ""
        status = avail_map.get(p.id)
        squad_availability.append({
            "name": p.name,
            "initials": initials,
            "gender": gender,
            "status": status,
        })

    in_count = sum(1 for p in squad_availability if p["status"] == "in")
    out_count = sum(1 for p in squad_availability if p["status"] == "out")
    no_reply_count = sum(1 for p in squad_availability if p["status"] is None)
    male_in = sum(1 for p in squad_availability if p["status"] == "in" and p["gender"] == "male")
    female_in = sum(1 for p in squad_availability if p["status"] == "in" and p["gender"] == "female")

    return render(request, "accounts/captain_dashboard.html", {
        "team": team,
        "season": team.season,
        "matches": matches,
        "next_fixture": next_fixture,
        "standings_rows": standings_rows,
        "league_position": league_position,
        "league_points": league_points,
        "total_teams": len(all_standings),
        "squad_availability": squad_availability,
        "in_count": in_count,
        "out_count": out_count,
        "no_reply_count": no_reply_count,
        "male_in": male_in,
        "female_in": female_in,
    })


@login_required
def player_dashboard_view(request):
    if request.user.role != "player":
        raise PermissionDenied
    from teams.models import Player
    from fixtures.models import PlayerAvailability
    player_record = (
        Player.objects.filter(user=request.user, registered=True, team__season__status="active")
        .select_related("team__season")
        .first()
    )
    if not player_record:
        messages.error(request, "You are not assigned to a team in an active season.")
        return redirect("home")
    team = player_record.team
    season = team.season
    upcoming_matches = (
        Match.objects.filter(season=season, status="scheduled")
        .filter(models.Q(team_a=team) | models.Q(team_b=team))
        .order_by("date", "time")
        .select_related("team_a", "team_b")
    )
    next_fixture = upcoming_matches.first()
    all_standings = list(
        Standing.objects.filter(season=season)
        .order_by("-points", "-wins")
        .select_related("team")
    )
    standing = None
    league_position = None
    for i, s in enumerate(all_standings):
        if s.team == team:
            standing = s
            league_position = i + 1
            break
    next_fixture_status = None
    if next_fixture:
        avail = PlayerAvailability.objects.filter(match=next_fixture, player=player_record).first()
        next_fixture_status = avail.status if avail else None
    standings_rows = [{"position": i + 1, "standing": s} for i, s in enumerate(all_standings)]
    return render(request, "accounts/player_dashboard.html", {
        "team": team,
        "season": season,
        "standing": standing,
        "next_fixture": next_fixture,
        "next_fixture_status": next_fixture_status,
        "upcoming_matches": upcoming_matches,
        "standings_rows": standings_rows,
        "league_position": league_position,
        "total_teams": len(all_standings),
    })


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})