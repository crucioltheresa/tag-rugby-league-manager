from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from seasons.models import Season
from .models import Standing


# Create your views here.
@login_required
def standings_view(request, season_id):
    season = get_object_or_404(Season, id=season_id)
    standings = Standing.objects.filter(season=season).select_related("team")
    rows = [{"position": i + 1, "standing": s} for i, s in enumerate(standings)]
    return render(
        request, "standings/standings_table.html", {"season": season, "rows": rows}
    )
