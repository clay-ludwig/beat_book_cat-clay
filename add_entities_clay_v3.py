import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def safe_list(value):
    if isinstance(value, list):
        return value
    return []


def clean(value, fallback="unknown"):
    if value is None:
        return fallback
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else fallback
    return str(value)


def parse_year(story):
    year = story.get("year")
    if isinstance(year, int):
        return year
    date = story.get("date", "")
    if isinstance(date, str) and len(date) >= 4 and date[:4].isdigit():
        return int(date[:4])
    return None


def first_sentence(text, limit=260):
    if not isinstance(text, str):
        return ""
    compact = " ".join(text.split())
    if not compact:
        return ""
    parts = compact.split(".")
    sentence = parts[0].strip() + ("." if len(parts) > 1 else "")
    if len(sentence) <= limit:
        return sentence
    return sentence[:limit].rstrip() + "..."


def load_stories(path):
    with open(path) as f:
        stories = json.load(f)

    valid = []
    for story in stories:
        if "entity_extraction_error" in story:
            continue
        if not story.get("primary_theme"):
            continue
        year = parse_year(story)
        if year is None:
            continue
        story["_year"] = year
        valid.append(story)
    return valid


def analyze(stories):
    by_year = defaultdict(lambda: {
        "count": 0,
        "themes": Counter(),
        "incident_types": Counter(),
        "severity": Counter(),
        "stories": [],
    })

    by_theme = defaultdict(lambda: {
        "count": 0,
        "by_year": Counter(),
        "by_season": Counter(),
        "incident_types": Counter(),
        "severity": Counter(),
        "stories": [],
    })

    by_season = defaultdict(lambda: {
        "count": 0,
        "themes": Counter(),
        "incident_types": Counter(),
        "stories": [],
    })

    locations = Counter()
    organizations = Counter()
    people = Counter()
    outcomes = Counter()

    for story in stories:
        year = story["_year"]
        theme = clean(story.get("primary_theme"))
        season = clean(story.get("season"), fallback="unknown")
        incident_type = clean(story.get("incident_type"))
        severity = clean(story.get("severity_level"))
        location_type = clean(story.get("location_type"), fallback="unknown")

        by_year[year]["count"] += 1
        by_year[year]["themes"][theme] += 1
        by_year[year]["incident_types"][incident_type] += 1
        by_year[year]["severity"][severity] += 1
        by_year[year]["stories"].append(story)

        by_theme[theme]["count"] += 1
        by_theme[theme]["by_year"][year] += 1
        by_theme[theme]["by_season"][season] += 1
        by_theme[theme]["incident_types"][incident_type] += 1
        by_theme[theme]["severity"][severity] += 1
        by_theme[theme]["stories"].append(story)

        by_season[season]["count"] += 1
        by_season[season]["themes"][theme] += 1
        by_season[season]["incident_types"][incident_type] += 1
        by_season[season]["stories"].append(story)

        locations[location_type] += 1
        outcomes[clean(story.get("outcome"))] += 1

        organizations.update(safe_list(story.get("organizations")))
        people.update(safe_list(story.get("people")))

    return {
        "by_year": dict(by_year),
        "by_theme": dict(by_theme),
        "by_season": dict(by_season),
        "locations": locations,
        "organizations": organizations,
        "people": people,
        "outcomes": outcomes,
    }


def trend_direction(counter_by_year):
    years = sorted(counter_by_year.keys())
    if len(years) < 2:
        return "steady"
    split = len(years) // 2
    early_years = years[:split]
    recent_years = years[split:]
    early_total = sum(counter_by_year[y] for y in early_years)
    recent_total = sum(counter_by_year[y] for y in recent_years)
    if recent_total > early_total * 1.2:
        return "up"
    if early_total > recent_total * 1.2:
        return "down"
    return "steady"


def has_meaningful_seasonality(by_season):
    seasons = ["winter", "spring", "summer", "fall"]
    counts = [by_season[s]["count"] for s in seasons if s in by_season]
    if len(counts) < 3:
        return False
    smallest = min(counts)
    largest = max(counts)
    if smallest == 0:
        return True
    return largest >= smallest * 1.3


def pick_examples(stories, limit=2):
    ranked = sorted(
        stories,
        key=lambda s: (
            clean(s.get("severity_level")) == "major",
            clean(s.get("date")),
        ),
        reverse=True,
    )
    return ranked[:limit]


def why_good_example(story):
    incident_type = clean(story.get("incident_type"), fallback="public safety incident")
    severity = clean(story.get("severity_level"), fallback="mixed")
    outcome = clean(story.get("outcome"), fallback="status evolving")
    return (
        f"Shows {incident_type} coverage with {severity} impact and an outcome of '{outcome}', "
        "which helps illustrate how this beat is reported in practice."
    )


def write_intro(stories, data):
    years = sorted(data["by_year"].keys())
    top_themes = [t for t, _ in Counter({k: v["count"] for k, v in data["by_theme"].items()}).most_common(4)]
    return (
        f"Welcome to the public safety beat. This guide is built from {len(stories)} previously summarized stories "
        f"across {years[0]}–{years[-1]}, so it focuses on real coverage patterns instead of one-off incidents.\n\n"
        "The goal is to get you up to speed quickly: what the beat has been covering, how that has shifted over time, "
        "and where useful follow-up angles are likely to be."
    )


def write_evolution_overview(data):
    years = sorted(data["by_year"].keys())
    lines = []
    for year in years:
        bucket = data["by_year"][year]
        top_themes = ", ".join([f"{t} ({c})" for t, c in bucket["themes"].most_common(3)])
        lines.append(f"- **{year}:** {bucket['count']} stories. Most frequent themes: {top_themes}.")

    theme_trends = []
    for theme, details in sorted(data["by_theme"].items(), key=lambda item: item[1]["count"], reverse=True)[:5]:
        direction = trend_direction(details["by_year"])
        if direction == "up":
            trend_label = "increasing"
        elif direction == "down":
            trend_label = "decreasing"
        else:
            trend_label = "fairly stable"
        theme_trends.append(f"- **{theme.title()}:** {trend_label} over the period.")

    return (
        "Coverage does not stay static here. Some themes gained momentum, others flattened out, and that matters for assignment planning.\n\n"
        "**Year-by-year view**\n"
        + "\n".join(lines)
        + "\n\n**Direction of major themes**\n"
        + "\n".join(theme_trends)
    )


def write_thematic_sections(data):
    sections = []
    top_themes = sorted(data["by_theme".strip()].items(), key=lambda item: item[1]["count"], reverse=True)[:5]

    for theme, details in top_themes:
        direction = trend_direction(details["by_year"])
        trend_text = {
            "up": "Coverage has generally increased.",
            "down": "Coverage has generally decreased.",
            "steady": "Coverage has stayed fairly steady.",
        }[direction]

        top_incidents = ", ".join([f"{i} ({c})" for i, c in details["incident_types"].most_common(3)])
        top_severity = ", ".join([f"{s} ({c})" for s, c in details["severity"].most_common(2)])

        season_bits = []
        for season in ["winter", "spring", "summer", "fall"]:
            if details["by_season"].get(season):
                season_bits.append(f"{season}: {details['by_season'][season]}")
        season_line = ", ".join(season_bits) if season_bits else "no clear seasonal split"

        section = []
        section.append(f"### {theme.title()}")
        section.append("")
        section.append(
            f"This theme appears in **{details['count']}** stories. {trend_text} "
            f"Most common incident types: {top_incidents}. Typical severity: {top_severity}."
        )
        section.append("")
        section.append(f"Seasonal signal: {season_line}.")
        section.append("")
        section.append("**Story examples**")

        for example in pick_examples(details["stories"], limit=2):
            summary = first_sentence(example.get("content", ""))
            section.append(
                f"- **{example.get('title', 'Untitled')}** ({example.get('date', 'unknown date')})"
            )
            section.append(f"  - Why it's a good example: {why_good_example(example)}")
            section.append(f"  - What happened: {summary}")

        sections.append("\n".join(section))

    return "\n\n".join(sections)


def write_seasonal_section(data):
    by_season = data["by_season"]
    if not has_meaningful_seasonality(by_season):
        return ""

    lines = [
        "## Seasonal Patterns (When Useful)",
        "",
        "Season is not the whole beat, but it does shape certain incident patterns. Here are the notable differences:",
        "",
    ]

    for season in ["winter", "spring", "summer", "fall"]:
        if season not in by_season:
            continue
        bucket = by_season[season]
        top_theme = bucket["themes"].most_common(1)
        theme_text = top_theme[0][0] if top_theme else "mixed"
        lines.append(
            f"- **{season.title()}:** {bucket['count']} stories; most common theme is {theme_text}."
        )

    return "\n".join(lines)


def write_contacts_and_orgs(data):
    people = [p for p, c in data["people"].most_common(12) if c > 1]
    orgs = [o for o, _ in data["organizations"].most_common(12)]

    lines = ["## Key People and Organizations", "", "These names show up often in the coverage and are useful starting points for sourcing:", ""]
    if people:
        lines.append("**People**")
        for person in people[:10]:
            lines.append(f"- {person}")
        lines.append("")

    if orgs:
        lines.append("**Organizations**")
        for org in orgs[:10]:
            lines.append(f"- {org}")

    return "\n".join(lines)


def write_followups(data):
    top_themes = sorted(data["by_theme"].items(), key=lambda item: item[1]["count"], reverse=True)
    up_trends = [theme for theme, details in top_themes if trend_direction(details["by_year"]) == "up"]
    top_locations = [loc for loc, _ in data["locations"].most_common(4) if loc != "unknown"]

    ideas = []
    if up_trends:
        ideas.append(f"How and why {up_trends[0]} coverage has increased over the last two years.")
    if len(up_trends) > 1:
        ideas.append(f"What agencies are doing differently around {up_trends[1]} incidents.")
    if top_locations:
        ideas.append(f"Why incidents cluster in {top_locations[0]} settings and whether prevention efforts are working.")
    ideas.append("Cases that remain 'under investigation': what is the status now?")
    ideas.append("Repeat locations or repeat offenders: are recurring patterns being addressed?")

    lines = [
        "## Potential Follow-Up Stories",
        "",
        "- " + "\n- ".join(ideas[:5]),
        "",
        "*Disclaimer: This dataset reflects previously published stories and may be outdated. Verify current facts, statuses, and agency details before reporting.*",
    ]
    return "\n".join(lines)


def build_beatbook(stories):
    data = analyze(stories)

    parts = [
        "# Public Safety Beat Book: Thematic Trends Over Time",
        "",
        write_intro(stories, data),
        "",
        "---",
        "",
        "## How Coverage Has Evolved",
        "",
        write_evolution_overview(data),
        "",
        "---",
        "",
        "## Major Themes in This Beat",
        "",
        write_thematic_sections(data),
    ]

    seasonal_section = write_seasonal_section(data)
    if seasonal_section:
        parts.extend(["", "---", "", seasonal_section])

    parts.extend([
        "",
        "---",
        "",
        write_contacts_and_orgs(data),
        "",
        "---",
        "",
        write_followups(data),
        "",
        "---",
        "",
        f"*Beatbook generated on {datetime.now().strftime('%Y-%m-%d')} from {len(stories)} pre-extracted stories in thematic_entities_stories.json.*",
        "",
    ])

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a reporter-friendly thematic beatbook from pre-extracted summaries and entities"
    )
    parser.add_argument("--input", default="thematic_entities_stories.json", help="Input JSON (default: thematic_entities_stories.json)")
    parser.add_argument("--output", default="thematic_beatbook_v3.md", help="Output markdown (default: thematic_beatbook_v3.md)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {args.input}")
        return

    stories = load_stories(args.input)
    if not stories:
        print("Error: no usable stories found (check entity extraction output).")
        return

    beatbook = build_beatbook(stories)
    with open(args.output, "w") as f:
        f.write(beatbook)

    print("=" * 60)
    print("BEATBOOK GENERATED")
    print("=" * 60)
    print(f"Input stories used: {len(stories)}")
    print(f"Output file: {args.output}")
    print("Note: Uses pre-extracted summaries and entities only (no story re-fetch).")


if __name__ == "__main__":
    main()
