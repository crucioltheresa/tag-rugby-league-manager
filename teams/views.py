from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from seasons.models import Season
from .models import Team
from .forms import TeamRegistrationForm


# Create your views here.
@login_required
def teams_list_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    teams_list = Team.objects.all()
    return render(request, "teams/teams_list.html", {"teams": teams_list})


@login_required
def create_team(request):
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
def edit_team(request, team_id):
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
def delete_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.user not in (team.captain, team.vice_captain):
        raise PermissionDenied
    if request.method == "POST":
        team.delete()
        messages.success(request, "Your team has been deleted successfully!")
        return redirect("home")
    return render(request, "teams/team_confirm_delete.html", {"team": team})
