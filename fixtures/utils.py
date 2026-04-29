from .models import Match
from teams.models import Team


def generate_round_robin(teams):
    # teams = Team.objects.all()
    n = len(teams)
    if n % 2 != 0:
        teams.append(None)
        n += 1

    rounds = []
    for round_num in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            team_a = teams[i]
            team_b = teams[n - 1 - i]
            if team_a is not None and team_b is not None:
                round_matches.append((team_a, team_b))
        rounds.append(round_matches)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return rounds


def generate_fixtures(season):
    teams = list(Team.objects.filter(season=season, status="approved"))
    if len(teams) < 2:
        raise ValueError("At least 2 approved teams are required to generate fixtures.")
    if Match.objects.filter(season=season).exists():
        raise ValueError("Fixtures have already been generated for this season.")

    # Build an infinite cycle of rounds (single then reversed for home/away)
    single = generate_round_robin(teams)
    double = [(team_b, team_a) for _, pairs in enumerate(single) for team_b, team_a in [p for p in pairs]]
    all_rounds = single + [[(b, a) for a, b in r] for r in single]

    for round_num in range(1, season.num_rounds + 1):
        # Cycle through available rounds if num_rounds exceeds the natural round-robin length
        round_matches = all_rounds[(round_num - 1) % len(all_rounds)]
        for team_a, team_b in round_matches:
            Match.objects.create(
                season=season,
                team_a=team_a,
                team_b=team_b,
                round_number=round_num,
                match_type="regular",
            )
