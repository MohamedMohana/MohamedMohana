#!/usr/bin/env python3

import datetime as dt
import html
import json
import os
import pathlib
import urllib.request
from collections import Counter


GRAPHQL_QUERY = """
query($login:String!) {
  user(login:$login) {
    name
    login
    followers {
      totalCount
    }
    following {
      totalCount
    }
    repositories(
      first: 100
      privacy: PUBLIC
      ownerAffiliations: OWNER
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      totalCount
      nodes {
        stargazerCount
        primaryLanguage {
          name
          color
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
    }
  }
}
""".strip()


def github_graphql(query: str, variables: dict[str, object], token: str) -> dict[str, object]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "MohamedMohana-profile-stats",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def format_number(value: int) -> str:
    return f"{value:,}"


def build_svg(user: dict[str, object]) -> str:
    repositories = user["repositories"]
    repo_nodes = repositories["nodes"]
    total_stars = sum(repo["stargazerCount"] for repo in repo_nodes)

    language_counts: Counter[str] = Counter()
    language_colors: dict[str, str] = {}
    for repo in repo_nodes:
        language = repo.get("primaryLanguage")
        if not language:
            continue
        name = language["name"]
        language_counts[name] += 1
        language_colors[name] = language.get("color") or "#94A3B8"

    top_languages = language_counts.most_common(5)
    metrics = [
        ("Public Repos", format_number(repositories["totalCount"])),
        ("Followers", format_number(user["followers"]["totalCount"])),
        ("Following", format_number(user["following"]["totalCount"])),
        ("Total Stars", format_number(total_stars)),
        (
            "Contributions (1y)",
            format_number(
                user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
            ),
        ),
    ]

    metric_cards = []
    card_positions = [
        (44, 102),
        (318, 102),
        (592, 102),
        (44, 214),
        (318, 214),
    ]
    for (label, value), (x, y) in zip(metrics, card_positions, strict=True):
        metric_cards.append(
            f"""
    <g transform="translate({x} {y})">
      <rect width="230" height="86" rx="20" fill="url(#cardFill)" stroke="rgba(255,255,255,0.08)" />
      <text x="20" y="36" class="metric-value">{html.escape(value)}</text>
      <text x="20" y="63" class="metric-label">{html.escape(label)}</text>
    </g>""".rstrip()
        )

    language_items = []
    start_y = 144
    for index, (name, count) in enumerate(top_languages):
        y = start_y + (index * 30)
        color = language_colors.get(name, "#94A3B8")
        language_items.append(
            f"""
    <g transform="translate(622 {y})">
      <circle cx="10" cy="0" r="6" fill="{html.escape(color)}" />
      <text x="28" y="5" class="language-name">{html.escape(name)}</text>
      <text x="220" y="5" text-anchor="end" class="language-count">{count} repos</text>
    </g>""".rstrip()
        )

    updated = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    title = html.escape(user.get("name") or user["login"])
    login = html.escape(user["login"])

    return f"""<svg width="900" height="340" viewBox="0 0 900 340" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{title} GitHub snapshot</title>
  <desc id="desc">Self-hosted GitHub profile snapshot with repository, follower, star, contribution, and language metrics.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="900" y2="340" gradientUnits="userSpaceOnUse">
      <stop stop-color="#120F22" />
      <stop offset="1" stop-color="#1F1636" />
    </linearGradient>
    <linearGradient id="cardFill" x1="0" y1="0" x2="230" y2="86" gradientUnits="userSpaceOnUse">
      <stop stop-color="#231A3D" />
      <stop offset="1" stop-color="#17112D" />
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#F472B6" />
      <stop offset="1" stop-color="#38BDF8" />
    </linearGradient>
    <style>
      .heading {{
        font: 700 28px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #F8FAFC;
      }}
      .subheading {{
        font: 500 14px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #CBD5E1;
      }}
      .metric-value {{
        font: 700 30px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #F8FAFC;
      }}
      .metric-label {{
        font: 500 14px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #C084FC;
      }}
      .section-label {{
        font: 700 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #F9A8D4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      .language-name {{
        font: 600 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #E2E8F0;
      }}
      .language-count {{
        font: 500 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #94A3B8;
      }}
      .footer {{
        font: 500 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        fill: #94A3B8;
      }}
    </style>
  </defs>

  <rect x="10" y="10" width="880" height="320" rx="28" fill="url(#bg)" />
  <rect x="10.5" y="10.5" width="879" height="319" rx="27.5" stroke="rgba(255,255,255,0.10)" />

  <circle cx="70" cy="64" r="18" fill="url(#accent)" opacity="0.95" />
  <rect x="96" y="47" width="244" height="9" rx="4.5" fill="url(#accent)" opacity="0.95" />
  <text x="44" y="108" class="heading">{title}</text>
  <text x="44" y="132" class="subheading">@{login} • self-hosted profile stats</text>

  {''.join(metric_cards)}

  <line x1="592" y1="112" x2="592" y2="290" stroke="rgba(255,255,255,0.08)" />
  <text x="622" y="118" class="section-label">Top Languages</text>
  {''.join(language_items)}

  <text x="44" y="308" class="footer">Generated in-repo from the GitHub GraphQL API</text>
  <text x="856" y="308" text-anchor="end" class="footer">Updated {updated}</text>
</svg>
"""


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    login = os.environ.get("PROFILE_LOGIN", "MohamedMohana")
    response = github_graphql(GRAPHQL_QUERY, {"login": login}, token)
    if response.get("errors"):
        raise SystemExit(json.dumps(response["errors"], indent=2))

    user = response["data"]["user"]
    output_path = pathlib.Path("assets/github-stats.svg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_svg(user), encoding="utf-8")


if __name__ == "__main__":
    main()
