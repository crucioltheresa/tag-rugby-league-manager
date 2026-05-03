from datetime import date
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
    all_teams = list(
        Team.objects.filter(
            models.Q(captain=request.user) | models.Q(vice_captain=request.user)
        ).select_related("season").distinct()
    )
    if not all_teams:
        return redirect("home")
    team_id = request.GET.get("team")
    team = next((t for t in all_teams if str(t.pk) == team_id), None) or all_teams[0]
    user_role_in_team = "Captain" if team.captain == request.user else "Vice Captain"
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

    registered_players = list(
        Player.objects.filter(team=team, registered=True).select_related("user")
    )

    # Include captain/VC player records even if they belong to a different team
    captain_users = [u for u in [team.captain, team.vice_captain] if u]
    captain_emails = [u.email for u in captain_users]
    existing_user_ids = {p.user_id for p in registered_players if p.user_id}
    extra_players = list(
        Player.objects.filter(
            models.Q(user__in=[u.id for u in captain_users]) | models.Q(email__in=captain_emails),
            registered=True,
        )
        .exclude(user_id__in=existing_user_ids)
        .select_related("user")
    )
    all_squad_players = registered_players + extra_players

    captain_player_record = next(
        (p for p in all_squad_players if p.user == request.user), None
    )
    next_fixture_status = None
    avail_map = {}
    if next_fixture:
        avail_map = {
            a.player_id: a.status
            for a in PlayerAvailability.objects.filter(match=next_fixture)
        }
        if captain_player_record:
            next_fixture_status = avail_map.get(captain_player_record.id)

    squad_availability = []
    for p in all_squad_players:
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
        "next_fixture_status": next_fixture_status,
        "all_teams": all_teams,
        "user_role_in_team": user_role_in_team,
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
        "today": date.today(),
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
    all_season_matches = list(
        Match.objects.filter(season=season)
        .order_by("round_number", "date", "time")
        .select_related("team_a", "team_b")
    )
    all_team_matches = [
        m for m in all_season_matches
        if m.team_a == team or m.team_b == team
    ]
    next_fixture = next(
        (m for m in all_team_matches if m.status == "scheduled"), None
    )
    matches = all_season_matches
    round_numbers = sorted(set(m.round_number for m in matches if m.round_number is not None))
    scheduled_rounds = sorted(set(
        m.round_number for m in matches
        if m.round_number is not None and m.status == "scheduled"
    ))
    default_round = scheduled_rounds[0] if scheduled_rounds else (round_numbers[-1] if round_numbers else None)
    active_round_param = request.GET.get("round")
    if active_round_param:
        try:
            active_round = int(active_round_param)
        except ValueError:
            active_round = default_round
    else:
        active_round = default_round
    if active_round is not None:
        matches = [m for m in matches if m.round_number == active_round]
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
        "matches": matches,
        "active_round": active_round,
        "round_numbers": round_numbers,
        "standings_rows": standings_rows,
        "league_position": league_position,
        "total_teams": len(all_standings),
        "today": date.today(),
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