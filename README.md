# Does Defense Win Championships?

A look at every Super Bowl team (Super Bowls I through LX, the 1966 through 2025 seasons) and how each one ranked in the regular season on offense and on defense.

**See the charts and write-up: https://s-milly.github.io/super-bowl-defense/**

Growing up, coaches would always say, "Defense wins championships." After a debate with my roommate about whether you'd rather have the best offense or the best defense in the league, I built this project to find out which has mattered more for winning a Super Bowl.

## What's here

| Path | What it is |
| --- | --- |
| `index.html` | The chart page, served by GitHub Pages |
| `site/page.html` | Source for the chart page (charts are drawn with plain JavaScript and SVG, no libraries) |
| `data/super_bowl_rankings.csv` / `.json` | The dataset |
| `data/raw/` | Untouched game results the dataset is built from |
| `scripts/build_dataset.py` | Builds the dataset from the raw game results |
| `scripts/build_page.py` | Builds `index.html` from `site/page.html` and the dataset |

## The data

`data/super_bowl_rankings.csv` (also available as `.json`) has 120 rows, one for each Super Bowl winner and loser.

| Column | Meaning |
| --- | --- |
| `super_bowl` | Super Bowl number (I to LX; Super Bowl 50 is written as `50`) |
| `season` | Regular season the game capped (Super Bowl LX was played in February 2026 and capped the 2025 season) |
| `result` | `Winner` or `Loser` |
| `team`, `opponent` | Team names as they were that season (e.g. Baltimore Colts, Oakland Raiders) |
| `franchise` | Current franchise code, to group a franchise across moves |
| `sb_points_for`, `sb_points_against` | Super Bowl score |
| `league` | `NFL`, or `AFL` for AFL teams before the 1970 merger |
| `teams_in_league` | Teams the ranks are out of |
| `reg_wins`, `reg_losses`, `reg_ties`, `reg_games` | Regular-season record |
| `points_scored`, `points_allowed` | Regular-season totals |
| `points_scored_per_game`, `points_allowed_per_game` | Totals per game (useful for 9-game 1982 and 17-game seasons since 2021) |
| `offense_rank` | Rank in points scored (1 = most) |
| `defense_rank` | Rank in points allowed (1 = fewest) |
| `offense_percentile`, `defense_percentile` | Rank scaled to league size: 1.0 = best, 0.0 = worst. Lets a 9-team AFL and a 32-team NFL be compared |
| `better_unit` | Which unit ranked higher that season: `Defense`, `Offense` or `Even` |

## Method

- Offense and defense are measured by **scoring**: points scored and points allowed over the regular season. Playoff games are not included.
- Ranks are computed from every regular-season game score, not copied from a table. Tied teams share the better rank (two teams tied for 2nd are both 2nd, next is 4th).
- Before the 1970 merger the AFL and NFL played separate schedules, so for 1966 to 1969 each team is ranked within its own league.
- The 1982 (9 games) and 1987 (15 games, including replacement games) strike seasons count as played.

## Sources

- **1966 to 1998:** [FiveThirtyEight `nfl-elo-game`](https://github.com/fivethirtyeight/nfl-elo-game) game results.
- **1999 to 2025:** [nflverse `nfldata`](https://github.com/nflverse/nfldata) game results.

Raw files are kept unchanged in `data/raw/`.

## Checks

Each run of `scripts/build_dataset.py`:

1. Confirms all 60 Super Bowl scores in the data match the official results.
2. Compares the two sources on every team's points scored and allowed for the 22 seasons they overlap (1999 to 2020). They agree on all of them.

## Rebuild

```
python3 scripts/build_dataset.py
python3 scripts/build_page.py
```

Python 3, standard library only. To add a new season, refresh `data/raw/nflverse_games.csv` from nflverse and add the game to `SUPER_BOWLS` in the script.

## Possible next additions

- Yardage ranks (total yards gained and allowed), a second way to measure offense and defense.
