from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Season, SeasonTimeSlot
from .forms import SeasonForm, SeasonTimeSlotForm
from fixtures.models import Match


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
    time_slots = season.time_slots.order_by("order", "time")
    timeslot_form = SeasonTimeSlotForm()
    has_fixtures = Match.objects.filter(season=season).exists()
    return render(request, "seasons/season_detail.html", {
        "season": season,
        "time_slots": time_slots,
        "timeslot_form": timeslot_form,
        "has_fixtures": has_fixtures,
    })


@login_required
def add_time_slot(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    if request.method == "POST":
        form = SeasonTimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.season = season
            slot.save()
            messages.success(request, "Kickoff time added.")
        else:
            messages.error(request, "Invalid time. Please try again.")
    return redirect("season_detail", season_id=season_id)


@login_required
def delete_time_slot(request, season_id, slot_id):
    if request.user.role != "admin":
        raise PermissionDenied
    slot = get_object_or_404(SeasonTimeSlot, id=slot_id, season_id=season_id)
    if request.method == "POST":
        slot.delete()
        messages.success(request, "Kickoff time removed.")
    return redirect("season_detail", season_id=season_id)
