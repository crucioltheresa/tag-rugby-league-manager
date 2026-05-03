from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from seasons.models import Season
from core.models import EmailWhitelist
from .models import Team, Player
from .forms import TeamRegistrationForm, AddPlayerForm


# Create your views here.
@login_required
def teams_list_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    teams_list = (
        Team.objects.all()
        .select_related("captain", "vice_captain", "season")
        .annotate(player_count=models.Count("player", filter=models.Q(player__registered=True)))
        .order_by("season__name", "name")
    )
    return render(request, "teams/teams_list.html", {"teams": teams_list})


@login_required
def team_create(request):
    if request.user.role not in ("captain", "vice_captain"):
        raise PermissionDenied
    active_season = Season.objects.filter(status="active").first()
    if not active_season:
        messages.error(request, "No active season available. Please contact the admin.")
        return redirect("home")
    if Team.objects.filter(captain=request.user, season=active_season).exists():
        messages.error(request, "You already have a team registered for this season.")
        return redirect("home")
    if request.method == "POST":
        form = TeamRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user
            team.season = active_season
            team.save()
            messages.success(request, "Your team has been created successfully")
            return redirect("home")
    else:
        form = TeamRegistrationForm(user=request.user)
    return render(request, "teams/team_form.html", {"form": form})


@login_required
def update_team_status(request, team_id):
    if request.user.role != "admin":
        raise PermissionDenied
    if request.method != "POST":
        return redirect("teams_list_view")

    team = get_object_or_404(Team, id=team_id)
    new_status = request.POST.get("status")
    if new_status not in ("approved", "rejected"):
        messages.error(request, "Invalid status value.")
        return redirect("teams_list_view")
    team.status = new_status
    team.save()
    messages.success(request, f"Submission status updated to {new_status}.")
    return redirect("teams_list_view")


@login_required
def team_edit(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.user not in (team.captain, team.vice_captain):
        raise PermissionDenied
    if request.method == "POST":
        form = TeamRegistrationForm(request.POST, instance=team, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your team has been updated successfully!")
            return redirect("home")
    elif request.method == "GET":
        form = TeamRegistrationForm(instance=team, user=request.user)
    return render(request, "teams/team_form.html", {"form": form, "team": team})


@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.user not in (team.captain, team.vice_captain):
        raise PermissionDenied
    if request.method == "POST":
        team.delete()
        messages.success(request, "Your team has been deleted successfully!")
        return redirect("home")
    return render(request, "teams/team_confirm_delete.html", {"team": team})


@login_required
def add_player(request):
    if request.user.role not in ("captain", "vice_captain"):
        raise PermissionDenied
    active_season = Season.objects.filter(status="active").first()
    if not active_season:
        messages.error(request, "No active season.")
        return redirect("home")
    team = (
        Team.objects.filter(season=active_season)
        .filter(models.Q(captain=request.user) | models.Q(vice_captain=request.user))
        .first()
    )
    if not team:
        messages.error(request, "You don't have a team for the active season.")
        return redirect("home")
    if request.method == "POST":
        form = AddPlayerForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            name = form.cleaned_data["name"]
            if Player.objects.filter(team=team, email=email).exists():
                messages.error(request, "That player is already in your squad.")
                return render(request, "teams/add_player.html", {"form": form})
            Player.objects.create(team=team, email=email, name=name)
            EmailWhitelist.objects.get_or_create(
                email=email, defaults={"source": "captain"}
            )
            messages.success(request, f"{name} added to your squad.")
            return redirect("squad_list")
    else:
        form = AddPlayerForm()
    return render(request, "teams/add_player.html", {"form": form})


@login_required
def squad_list(request):
    if request.user.role not in ("captain", "vice_captain"):
        raise PermissionDenied
    active_season = Season.objects.filter(status="active").first()
    if not active_season:
        messages.error(request, "No active season.")
        return redirect("home")
    team = (
        Team.objects.filter(season=active_season)
        .filter(models.Q(captain=request.user) | models.Q(vice_captain=request.user))
        .first()
    )
    if not team:
        messages.error(request, "You don't have a team for the active season.")
        return redirect("home")
    players = Player.objects.filter(team=team).select_related("user").order_by("-registered", "name")
    return render(request, "teams/squad_list.html", {"team": team, "players": players})


@login_required
def set_vice_captain(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    team = player.team
    if request.user != team.captain:
        raise PermissionDenied
    if request.method != "POST":
        return redirect("squad_list")
    if not player.user:
        messages.error(request, "This player doesn't have an account yet and cannot be set as vice captain.")
        return redirect("squad_list")
    # Demote the previous VC back to player (only if they were promoted from player, not if they're a captain elsewhere)
    if team.vice_captain and team.vice_captain != player.user:
        prev_vc = team.vice_captain
        if prev_vc.role == "vice_captain":
            if Team.objects.filter(captain=prev_vc).exists():
                prev_vc.role = "captain"
            else:
                prev_vc.role = "player"
            prev_vc.save()
    # Promote the new VC (only change role if they're currently a player)
    if player.user.role == "player":
        player.user.role = "vice_captain"
        player.user.save()
    team.vice_captain = player.user
    team.save()
    messages.success(request, f"{player.name} is now the vice captain.")
    return redirect("squad_list")


@login_required
def remove_player(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    if request.user not in (player.team.captain, player.team.vice_captain):
        raise PermissionDenied
    if request.method == "POST":
        if not player.user:
            EmailWhitelist.objects.filter(email=player.email).delete()
        player.delete()
    return redirect("squad_list")
