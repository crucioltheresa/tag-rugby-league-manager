from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from itertools import groupby
from .utils import generate_fixtures
from .forms import MatchForm, ScheduleRoundForm, BulkScheduleForm
from datetime import timedelta
import json
from seasons.models import Season
from teams.models import Team
from .models import Match


@login_required
def my_fixtures(request):
    team = (
        Team.objects.filter(captain=request.user, season__status="active").first()
        or Team.objects.filter(vice_captain=request.user, season__status="active").first()
    )
    if not team:
        messages.error(request, "You are not assigned to a team in an active season.")
        return redirect("home")

    matches = (
        Match.objects.filter(season=team.season)
        .filter(models.Q(team_a=team) | models.Q(team_b=team))
        .order_by("round_number", "date", "time")
        .select_related("team_a", "team_b")
    )
    rounds = [
        {"round_number": rn, "matches": list(group)}
        for rn, group in groupby(matches, key=lambda m: m.round_number)
    ]
    return render(request, "fixtures/my_fixtures.html", {
        "team": team,
        "season": team.season,
        "rounds": rounds,
    })


@login_required
def generate_fixture_view(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    try:
        generate_fixtures(season)
        messages.success(request, "Fixtures generated successfully!")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("season_detail", season_id=season_id)


@login_required
def delete_fixtures(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    match_count = Match.objects.filter(season=season).count()
    if request.method == "POST":
        Match.objects.filter(season=season).delete()
        messages.success(request, f"All {match_count} fixtures for {season.name} have been deleted.")
        return redirect("season_detail", season_id=season_id)
    return render(request, "fixtures/confirm_delete_fixtures.html", {
        "season": season,
        "match_count": match_count,
    })


@login_required
def current_fixtures(request):
    # Captains/vice-captains go directly to their team's season
    if request.user.role in ("captain", "vice_captain"):
        team = (
            Team.objects.filter(captain=request.user, season__status="active").first()
            or Team.objects.filter(vice_captain=request.user, season__status="active").first()
        )
        if team:
            return redirect("fixture_list", season_id=team.season_id)

    # Admin and everyone else: first active season, or seasons list if none
    season = Season.objects.filter(status="active").first()
    if season:
        return redirect("fixture_list", season_id=season.id)

    if request.user.role == "admin":
        messages.error(request, "No active season. Create one first.")
        return redirect("seasons_list_view")

    messages.error(request, "There is no active season.")
    return redirect("home")


@login_required
def fixture_list(request, season_id):
    season = get_object_or_404(Season, id=season_id)
    matches = list(
        Match.objects.filter(season=season)
        .order_by("round_number", "date", "time")
        .select_related("team_a", "team_b")
    )
    rounds = [
        {"round_number": rn, "matches": list(group)}
        for rn, group in groupby(matches, key=lambda m: m.round_number)
    ]
    color_map = {"played": "#2d5c1a", "cancelled": "#dc3545", "scheduled": "#6c757d"}
    calendar_events = json.dumps([
        {
            "title": f"R{m.round_number}: {m.team_a.name} vs {m.team_b.name}",
            "start": (
                f"{m.date}T{m.time}" if m.time else str(m.date)
            ),
            "color": color_map.get(m.status, "#6c757d"),
            "extendedProps": {
                "round": m.round_number,
                "status": m.get_status_display(),
                "pitch": m.pitch or "—",
            },
        }
        for m in matches if m.date
    ])
    return render(request, "fixtures/fixtures_list.html", {
        "season": season,
        "rounds": rounds,
        "calendar_events": calendar_events,
    })


@login_required
def schedule_round(request, season_id, round_number):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    matches = list(
        Match.objects.filter(season=season, round_number=round_number)
        .order_by("id")
        .select_related("team_a", "team_b")
    )
    if not matches:
        messages.error(request, f"No matches found for round {round_number}.")
        return redirect("fixture_list", season_id=season_id)

    if request.method == "POST":
        form = ScheduleRoundForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data["date"]
            time_slots = list(season.time_slots.order_by("order", "time"))
            slots = [
                (ts.time, f"Pitch {p}")
                for ts in time_slots
                for p in range(1, season.num_pitches + 1)
            ]
            for i, match in enumerate(matches):
                match.date = date
                match.time = slots[i][0] if i < len(slots) else None
                match.pitch = slots[i][1] if i < len(slots) else ""
                match.save()
            messages.success(request, f"Round {round_number} scheduled for {date}.")
            return redirect("fixture_list", season_id=season_id)
    else:
        form = ScheduleRoundForm(initial={"date": matches[0].date})

    time_slots = list(season.time_slots.order_by("order", "time"))
    slots = [
        (ts.time, f"Pitch {p}")
        for ts in time_slots
        for p in range(1, season.num_pitches + 1)
    ]
    match_slots = [
        {"match": m, "time": slots[i][0] if i < len(slots) else None, "pitch": slots[i][1] if i < len(slots) else "—"}
        for i, m in enumerate(matches)
    ]
    return render(request, "fixtures/schedule_round.html", {
        "form": form,
        "season": season,
        "round_number": round_number,
        "match_slots": match_slots,
        "time_slots": time_slots,
    })


@login_required
def bulk_schedule(request, season_id):
    if request.user.role != "admin":
        raise PermissionDenied
    season = get_object_or_404(Season, id=season_id)
    time_slots = list(season.time_slots.order_by("order", "time"))
    slots = [
        (ts.time, f"Pitch {p}")
        for ts in time_slots
        for p in range(1, season.num_pitches + 1)
    ]
    round_numbers = (
        Match.objects.filter(season=season)
        .values_list("round_number", flat=True)
        .distinct()
        .order_by("round_number")
    )

    if request.method == "POST":
        form = BulkScheduleForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            interval = form.cleaned_data["interval_days"]
            overwrite = form.cleaned_data["overwrite"]
            scheduled = 0

            for round_number in round_numbers:
                matches = list(
                    Match.objects.filter(season=season, round_number=round_number).order_by("id")
                )
                if not overwrite and matches[0].date:
                    continue
                round_date = start_date + timedelta(days=(round_number - 1) * interval)
                for i, match in enumerate(matches):
                    match.date = round_date
                    match.time = slots[i][0] if i < len(slots) else None
                    match.pitch = slots[i][1] if i < len(slots) else ""
                    match.save()
                scheduled += 1

            messages.success(request, f"{scheduled} round(s) scheduled successfully.")
            return redirect("fixture_list", season_id=season_id)
    else:
        form = BulkScheduleForm(initial={"interval_days": 7})

    # Build a preview of what dates would be assigned
    preview = [
        {
            "round_number": rn,
            "already_scheduled": Match.objects.filter(season=season, round_number=rn).exclude(date=None).exists(),
        }
        for rn in round_numbers
    ]

    return render(request, "fixtures/bulk_schedule.html", {
        "form": form,
        "season": season,
        "preview": preview,
        "has_time_slots": bool(time_slots),
    })
