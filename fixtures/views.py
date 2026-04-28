from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .utils import generate_fixtures
from seasons.models import Season


# Create your views here.
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
    return redirect("fixtures_list")
