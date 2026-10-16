"""
Build the Super Bowl offense/defense rankings dataset.

For every Super Bowl (I through LX, 1966-2025 seasons) this finds both teams'
regular-season scoring offense rank (points scored) and scoring defense rank
(points allowed) within their league that season.

Rankings are computed from game-by-game regular-season scores:
  - 1966-1998 seasons: FiveThirtyEight nfl-elo-game (data/raw/fivethirtyeight_nfl_games.csv)
  - 1999-2025 seasons: nflverse nfldata (data/raw/nflverse_games.csv)
Where the two sources overlap (1999-2020) the script checks they agree.

Rank 1 = most points scored (offense) / fewest points allowed (defense).
Tied teams share the better rank (standard competition ranking, "1224").
For 1966-1969, AFL and NFL teams are ranked within their own league,
since the leagues played separate schedules.

Run:  python3 scripts/build_dataset.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

# nflverse uses era-specific codes; map them onto one code per franchise.
NFLVERSE_FRANCHISE = {"LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV", "LV": "LV", "WAS": "WSH"}
FTE_FRANCHISE = {"OAK": "LV"}

AFL_TEAMS = {"BUF", "NYJ", "NE", "MIA", "KC", "LV", "LAC", "DEN", "TEN", "CIN"}

# Franchise name by season: list of (first season, name), newest last.
NAMES = {
    "ARI": [(1960, "St. Louis Cardinals"), (1988, "Phoenix Cardinals"), (1994, "Arizona Cardinals")],
    "ATL": [(1966, "Atlanta Falcons")],
    "BAL": [(1996, "Baltimore Ravens")],
    "BUF": [(1960, "Buffalo Bills")],
    "CAR": [(1995, "Carolina Panthers")],
    "CHI": [(1920, "Chicago Bears")],
    "CIN": [(1968, "Cincinnati Bengals")],
    "CLE": [(1946, "Cleveland Browns")],
    "DAL": [(1960, "Dallas Cowboys")],
    "DEN": [(1960, "Denver Broncos")],
    "DET": [(1934, "Detroit Lions")],
    "GB":  [(1921, "Green Bay Packers")],
    "HOU": [(2002, "Houston Texans")],
    "IND": [(1953, "Baltimore Colts"), (1984, "Indianapolis Colts")],
    "JAX": [(1995, "Jacksonville Jaguars")],
    "KC":  [(1963, "Kansas City Chiefs")],
    "LAC": [(1961, "San Diego Chargers"), (2017, "Los Angeles Chargers")],
    "LAR": [(1946, "Los Angeles Rams"), (1995, "St. Louis Rams"), (2016, "Los Angeles Rams")],
    "LV":  [(1960, "Oakland Raiders"), (1982, "Los Angeles Raiders"), (1995, "Oakland Raiders"), (2020, "Las Vegas Raiders")],
    "MIA": [(1966, "Miami Dolphins")],
    "MIN": [(1961, "Minnesota Vikings")],
    "NE":  [(1960, "Boston Patriots"), (1971, "New England Patriots")],
    "NO":  [(1967, "New Orleans Saints")],
    "NYG": [(1925, "New York Giants")],
    "NYJ": [(1963, "New York Jets")],
    "PHI": [(1933, "Philadelphia Eagles")],
    "PIT": [(1940, "Pittsburgh Steelers")],
    "SEA": [(1976, "Seattle Seahawks")],
    "SF":  [(1950, "San Francisco 49ers")],
    "TB":  [(1976, "Tampa Bay Buccaneers")],
    "TEN": [(1960, "Houston Oilers"), (1997, "Tennessee Oilers"), (1999, "Tennessee Titans")],
    "WSH": [(1937, "Washington Redskins"), (2020, "Washington Football Team"), (2022, "Washington Commanders")],
}

# Official results, used to check the Super Bowl game found in the data.
# (number, season, winner, winner pts, loser, loser pts)
SUPER_BOWLS = [
    ("I", 1966, "GB", 35, "KC", 10), ("II", 1967, "GB", 33, "LV", 14),
    ("III", 1968, "NYJ", 16, "IND", 7), ("IV", 1969, "KC", 23, "MIN", 7),
    ("V", 1970, "IND", 16, "DAL", 13), ("VI", 1971, "DAL", 24, "MIA", 3),
    ("VII", 1972, "MIA", 14, "WSH", 7), ("VIII", 1973, "MIA", 24, "MIN", 7),
    ("IX", 1974, "PIT", 16, "MIN", 6), ("X", 1975, "PIT", 21, "DAL", 17),
    ("XI", 1976, "LV", 32, "MIN", 14), ("XII", 1977, "DAL", 27, "DEN", 10),
    ("XIII", 1978, "PIT", 35, "DAL", 31), ("XIV", 1979, "PIT", 31, "LAR", 19),
    ("XV", 1980, "LV", 27, "PHI", 10), ("XVI", 1981, "SF", 26, "CIN", 21),
    ("XVII", 1982, "WSH", 27, "MIA", 17), ("XVIII", 1983, "LV", 38, "WSH", 9),
    ("XIX", 1984, "SF", 38, "MIA", 16), ("XX", 1985, "CHI", 46, "NE", 10),
    ("XXI", 1986, "NYG", 39, "DEN", 20), ("XXII", 1987, "WSH", 42, "DEN", 10),
    ("XXIII", 1988, "SF", 20, "CIN", 16), ("XXIV", 1989, "SF", 55, "DEN", 10),
    ("XXV", 1990, "NYG", 20, "BUF", 19), ("XXVI", 1991, "WSH", 37, "BUF", 24),
    ("XXVII", 1992, "DAL", 52, "BUF", 17), ("XXVIII", 1993, "DAL", 30, "BUF", 13),
    ("XXIX", 1994, "SF", 49, "LAC", 26), ("XXX", 1995, "DAL", 27, "PIT", 17),
    ("XXXI", 1996, "GB", 35, "NE", 21), ("XXXII", 1997, "DEN", 31, "GB", 24),
    ("XXXIII", 1998, "DEN", 34, "ATL", 19), ("XXXIV", 1999, "LAR", 23, "TEN", 16),
    ("XXXV", 2000, "BAL", 34, "NYG", 7), ("XXXVI", 2001, "NE", 20, "LAR", 17),
    ("XXXVII", 2002, "TB", 48, "LV", 21), ("XXXVIII", 2003, "NE", 32, "CAR", 29),
    ("XXXIX", 2004, "NE", 24, "PHI", 21), ("XL", 2005, "PIT", 21, "SEA", 10),
    ("XLI", 2006, "IND", 29, "CHI", 17), ("XLII", 2007, "NYG", 17, "NE", 14),
    ("XLIII", 2008, "PIT", 27, "ARI", 23), ("XLIV", 2009, "NO", 31, "IND", 17),
    ("XLV", 2010, "GB", 31, "PIT", 25), ("XLVI", 2011, "NYG", 21, "NE", 17),
    ("XLVII", 2012, "BAL", 34, "SF", 31), ("XLVIII", 2013, "SEA", 43, "DEN", 8),
    ("XLIX", 2014, "NE", 28, "SEA", 24), ("50", 2015, "DEN", 24, "CAR", 10),
    ("LI", 2016, "NE", 34, "ATL", 28), ("LII", 2017, "PHI", 41, "NE", 33),
    ("LIII", 2018, "NE", 13, "LAR", 3), ("LIV", 2019, "KC", 31, "SF", 20),
    ("LV", 2020, "TB", 31, "KC", 9), ("LVI", 2021, "LAR", 23, "CIN", 20),
    ("LVII", 2022, "KC", 38, "PHI", 35), ("LVIII", 2023, "KC", 25, "SF", 22),
    ("LIX", 2024, "PHI", 40, "KC", 22), ("LX", 2025, "SEA", 29, "NE", 13),
]


def name_of(team, season):
    return [n for start, n in NAMES[team] if start <= season][-1]


def load_games():
    """Return {season: {"reg": [(team_a, pts_a, team_b, pts_b)], "post": [...]}} per source."""
    fte, nflv = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    with open(RAW / "fivethirtyeight_nfl_games.csv") as f:
        for r in csv.DictReader(f):
            s = int(r["season"])
            if s < 1966:
                continue
            g = (FTE_FRANCHISE.get(r["team1"], r["team1"]), int(r["score1"]),
                 FTE_FRANCHISE.get(r["team2"], r["team2"]), int(r["score2"]))
            fte[s]["post" if r["playoff"] == "1" else "reg"].append(g)
    with open(RAW / "nflverse_games.csv") as f:
        for r in csv.DictReader(f):
            if not r["home_score"]:
                continue  # not played yet
            s = int(r["season"])
            g = (NFLVERSE_FRANCHISE.get(r["away_team"], r["away_team"]), int(r["away_score"]),
                 NFLVERSE_FRANCHISE.get(r["home_team"], r["home_team"]), int(r["home_score"]))
            nflv[s]["reg" if r["game_type"] == "REG" else "post"].append(g)
            if r["game_type"] == "SB":
                nflv[s]["sb"].append(g)
    return fte, nflv


def season_totals(games):
    t = defaultdict(lambda: {"pf": 0, "pa": 0, "w": 0, "l": 0, "t": 0, "g": 0})
    for a, pa, b, pb in games:
        for team, us, them in ((a, pa, pb), (b, pb, pa)):
            row = t[team]
            row["pf"] += us
            row["pa"] += them
            row["g"] += 1
            row["w" if us > them else "l" if us < them else "t"] += 1
    return t


def rank(values, team, best_high):
    v = values[team]
    better = sum(1 for x in values.values() if (x > v if best_high else x < v))
    return better + 1


def league_of(team, season):
    if season <= 1969:
        return "AFL" if team in AFL_TEAMS else "NFL"
    return "NFL"


def main():
    fte, nflv = load_games()
    problems = []

    # Cross-check the overlapping seasons.
    for s in range(1999, 2021):
        a, b = season_totals(fte[s]["reg"]), season_totals(nflv[s]["reg"])
        for team in set(a) | set(b):
            if (a[team]["pf"], a[team]["pa"]) != (b[team]["pf"], b[team]["pa"]):
                problems.append(f"{s} {team}: 538 {a[team]['pf']}-{a[team]['pa']} vs nflverse {b[team]['pf']}-{b[team]['pa']}")

    rows = []
    for num, season, win, wpts, lose, lpts in SUPER_BOWLS:
        src = fte if season < 1999 else nflv
        reg = season_totals(src[season]["reg"])

        # Confirm the Super Bowl itself is in the data with the official score.
        sb_games = src[season]["sb"] if season >= 1999 else src[season]["post"][-1:]
        found = any({(a, pa), (b, pb)} == {(win, wpts), (lose, lpts)} for a, pa, b, pb in sb_games)
        if not found:
            problems.append(f"SB {num}: game {win} {wpts}-{lpts} {lose} not found in data")

        for team, result, pts, opp_pts, opp in ((win, "Winner", wpts, lpts, lose), (lose, "Loser", lpts, wpts, win)):
            lg = league_of(team, season)
            peers = {t: v for t, v in reg.items() if league_of(t, season) == lg}
            pf = {t: v["pf"] for t, v in peers.items()}
            pa = {t: v["pa"] for t, v in peers.items()}
            me = reg[team]
            n = len(peers)
            off_rank, def_rank = rank(pf, team, True), rank(pa, team, False)
            rows.append({
                "super_bowl": num,
                "season": season,
                "result": result,
                "team": name_of(team, season),
                "franchise": team,
                "opponent": name_of(opp, season),
                "sb_points_for": pts,
                "sb_points_against": opp_pts,
                "league": lg,
                "teams_in_league": n,
                "reg_wins": me["w"],
                "reg_losses": me["l"],
                "reg_ties": me["t"],
                "reg_games": me["g"],
                "points_scored": me["pf"],
                "points_allowed": me["pa"],
                "points_scored_per_game": round(me["pf"] / me["g"], 1),
                "points_allowed_per_game": round(me["pa"] / me["g"], 1),
                "offense_rank": off_rank,
                "defense_rank": def_rank,
                # 1.0 = best in league, 0.0 = worst; lets eras with 24-32 teams be compared.
                "offense_percentile": round(1 - (off_rank - 1) / (n - 1), 3),
                "defense_percentile": round(1 - (def_rank - 1) / (n - 1), 3),
                "better_unit": "Defense" if def_rank < off_rank else "Offense" if off_rank < def_rank else "Even",
            })

    with open(OUT / "super_bowl_rankings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "super_bowl_rankings.json", "w") as f:
        json.dump(rows, f, indent=2)

    print(f"{len(rows)} team-seasons written")
    print("Problems:" if problems else "No problems: every Super Bowl score matched and the sources agree.")
    for p in problems:
        print("  ", p)


if __name__ == "__main__":
    main()
