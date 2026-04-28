from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Season
from .forms import SeasonForm


# Create your views here.
@login_required
def seasons_list_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    seasons_list = Season.objects.all()
    return render(request, "seasons/seasons_list.html", {"seasons": seasons_list})


@login_required
def season_create(request):
    if request.user.role != "admin":
        raise PermissionDenied
    if request.method == "POST":
        form = SeasonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your season has been created successfully!")
            return redirect("seasons_list_view")
    else:
        form = SeasonForm()
    return render(request, "seasons/season_form.html", {"form": form})


@login_required
def season_edit(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    if request.method == "POST":
        form = SeasonForm(request.POST, instance=season)
        if form.is_valid():
            form.save()
            messages.success(request, "Your season has been updated successfully!")
            return redirect("seasons_list_view")
    elif request.method == "GET":
        form = SeasonForm(instance=season)
    return render(request, "seasons/season_form.html", {"form": form, "season": season})


@login_required
def season_delete(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    if request.method == "POST":
        season.delete()
        messages.success(request, "Your season has been deleted successfully!")
        return redirect("seasons_list_view")
    return render(request, "seasons/season_confirm_delete.html", {"season": season})


@login_required
def season_detail(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    return render(request, "seasons/season_detail.html", {"season": season})
