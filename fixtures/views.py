from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db import models
from itertools import groupby
from .utils import generate_fixtures
from .forms import MatchForm, MatchResultForm, ScheduleRoundForm, BulkScheduleForm
from datetime import timedelta
from seasons.models import Season
from teams.models import Team
from .models import Match
from standings.utils import update_standings


@login_required
def my_fixtures(request):
    team = (
        Team.objects.filter(captain=request.user, season__status="active").first()
        or Team.objects.filter(
            vice_captain=request.user, season__status="active"
        ).first()
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
    return render(
        request,
        "fixtures/my_fixtures.html",
        {
            "team": team,
            "season": team.season,
            "matches": matches,
        },
    )


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
        messages.success(
            request, f"All {match_count} fixtures for {season.name} have been deleted."
        )
        return redirect("season_detail", season_id=season_id)
    return render(
        request,
        "fixtures/confirm_delete_fixtures.html",
        {
            "season": season,
            "match_count": match_count,
        },
    )


@login_required
def current_fixtures(request):
    # Captains/vice-captains go directly to their team's season
    if request.user.role in ("captain", "vice_captain"):
        team = (
            Team.objects.filter(captain=request.user, season__status="active").first()
            or Team.objects.filter(
                vice_captain=request.user, season__status="active"
            ).first()
        )
        if team:
            return redirect("fixture_list", season_id=team.season_id)

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
        .order_by("date", "time", "round_number")
        .select_related("team_a", "team_b")
    )
    scheduled = [m for m in matches if m.date]
    unscheduled = [m for m in matches if not m.date]

    date_groups = [
        {"date": d, "matches": list(group)}
        for d, group in groupby(scheduled, key=lambda m: m.date)
    ]
    return render(
        request,
        "fixtures/fixtures_list.html",
        {
            "season": season,
            "date_groups": date_groups,
            "unscheduled": unscheduled,
            "has_matches": bool(matches),
        },
    )


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
        {
            "match": m,
            "time": slots[i][0] if i < len(slots) else None,
            "pitch": slots[i][1] if i < len(slots) else "—",
        }
        for i, m in enumerate(matches)
    ]
    return render(
        request,
        "fixtures/schedule_round.html",
        {
            "form": form,
            "season": season,
            "round_number": round_number,
            "match_slots": match_slots,
            "time_slots": time_slots,
        },
    )


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
                    Match.objects.filter(
                        season=season, round_number=round_number
                    ).order_by("id")
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
            "already_scheduled": Match.objects.filter(season=season, round_number=rn)
            .exclude(date=None)
            .exists(),
        }
        for rn in round_numbers
    ]

    return render(
        request,
        "fixtures/bulk_schedule.html",
        {
            "form": form,
            "season": season,
            "preview": preview,
            "has_time_slots": bool(time_slots),
        },
    )


@login_required
def ics_match(request, fixture_id):
    from datetime import datetime, time, timedelta
    from icalendar import Calendar, Event

    match = get_object_or_404(Match, id=fixture_id)

    if not match.date:
        messages.error(request, "This match has no date scheduled yet.")
        return redirect("captain_dashboard")

    match_time = match.time if match.time else time(0, 0)
    start = datetime.combine(match.date, match_time)
    end = start + timedelta(hours=1)

    cal = Calendar()
    cal.add("prodid", "-//TRLM//Tag Rugby//EN")
    cal.add("version", "2.0")

    event = Event()
    event.add(
        "summary",
        f"{match.team_a.name} vs {match.team_b.name} - Round {match.round_number}",
    )
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("location", match.season.get_venue_display())
    event.add("description", match.season.name)
    event["uid"] = f"match-{match.id}@trlm"

    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="match_{match.id}.ics"'
    return response


@login_required
def match_edit(request, match_id):
    if request.user.role != "admin":
        raise PermissionDenied
    match = get_object_or_404(Match, id=match_id)
    if request.method == "POST":
        form = MatchForm(
            request.POST,
            instance=match,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Your match has been updated successfully!")
            return redirect("fixture_list", season_id=match.season_id)
    elif request.method == "GET":
        form = MatchForm(instance=match)
    return render(request, "fixtures/match_form.html", {"form": form, "match": match})


@login_required
def match_result(request, match_id):
    if request.user.role != "admin":
        raise PermissionDenied
    match = get_object_or_404(Match, id=match_id)
    if request.method == "POST":
        form = MatchResultForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save(commit=False)
            match.status = "played"
            match.save()
            update_standings(match.season)
            messages.success(
                request, "Score has been added to your match successfully!"
            )
            return redirect("fixture_list", season_id=match.season_id)
    elif request.method == "GET":
        form = MatchResultForm(instance=match)
    return render(request, "fixtures/match_result.html", {"form": form, "match": match})


@login_required
def match_cancel(request, match_id):
    if request.user.role != "admin":
        raise PermissionDenied
    match = get_object_or_404(Match, id=match_id)
    if request.method == "POST":
        match.status = "cancelled"
        match.save()
        messages.success(
            request,
            f"Match {match.team_a.name} vs {match.team_b.name} has been cancelled.",
        )
        return redirect("fixture_list", season_id=match.season_id)
    return render(request, "fixtures/match_cancel.html", {"match": match})
