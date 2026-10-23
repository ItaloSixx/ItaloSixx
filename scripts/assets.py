#!/usr/bin/env python3
"""SVGs do perfil — arcade, alimentados por dados reais do GitHub.

Gera:
  assets/hero.svg      marquise (nome + stack principal)
  assets/game.svg      attract mode com HUD de commits/frequência
  assets/leaderboard.svg  ranking de repos por commits
  assets/rhythm.svg    frequência: heatmap de 26 semanas + dia da semana

Sem dependências externas (só stdlib). Uso: GH_TOKEN=... python scripts/assets.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta

USER = os.environ.get("PROFILE_USER", "ItaloSixx")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'

BLACK, DARK, LINE = "#000000", "#0A0A0C", "#232329"
INK, MUTED, DIM = "#FFFFFF", "#A8A8B4", "#84848F"
NEON, NEON2, WARM, RED = "#3DF5A8", "#5AC8FF", "#FFB84D", "#FF4D6A"
GAME_URL = "https://italosixx.github.io/ItaloSixx/"

# stack principal declarada + cor
STACK = [
    ("JAVA", "backend · android", "#F0A03C", 0.42),
    ("PHP", "laravel · apis", "#8B93E8", 0.34),
    ("FLUTTER", "mobile", "#39D2C0", 0.24),
    ("C", "firmware · esp32", "#B9BEC6", 0.20),
    ("PYTHON", "dados · scripts", "#5AC8FF", 0.16),
]

CRAB = ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.",
        "XXXXXXXXXXX", "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."]
SQUID = ["...XX...", "..XXXX..", ".XXXXXX.", "XX.XX.XX",
         "XXXXXXXX", "..X..X..", ".X.XX.X.", "X.X..X.X"]
OCTOPUS = ["....XXXX....", ".XXXXXXXXXX.", "XXXXXXXXXXXX", "XXX..XX..XXX",
           "XXXXXXXXXXXX", "...XX..XX...", "..XX.XX.XX..", "XX........XX"]
SHIP = [".....X.....", "....XXX....", "....XXX....", ".XXXXXXXXX.",
        "XXXXXXXXXXX", "XXXXXXXXXXX", "XX.XXXXX.XX", "X...X.X...X"]


def sprite(rows, x, y, px, color):
    out = []
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch == "X":
                out.append(f'<rect x="{x + rx * px:g}" y="{y + ry * px:g}" width="{px:g}" height="{px:g}"/>')
    return f'<g fill="{color}" shape-rendering="crispEdges">{"".join(out)}</g>'


# ------------------------------------------------------------------ dados

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount date } } }
    }
    repoList: repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        name stargazerCount primaryLanguage { name } releases { totalCount }
        defaultBranchRef { target { ... on Commit { history(first: 100) { totalCount pageInfo { hasNextPage endCursor } nodes { committedDate } } } } }
      }
    }
  }
}
"""


def fetch() -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "profile-assets"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]


PAGE_QUERY = """
query($login: String!, $name: String!, $cursor: String!) {
  user(login: $login) {
    repository(name: $name) {
      defaultBranchRef { target { ... on Commit { history(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor } nodes { committedDate }
      } } } }
    }
  }
}
"""


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "profile-assets"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]


def more_dates(name: str, cursor: str) -> list:
    """Pagina o histórico — history(first:100) só devolve 100 datas por repo."""
    out = []
    for _ in range(20):  # trava de segurança
        repo = gql(PAGE_QUERY, {"login": USER, "name": name, "cursor": cursor})["repository"]
        hist = ((repo["defaultBranchRef"] or {}).get("target") or {}).get("history")
        if not hist:
            break
        out += [x["committedDate"][:10] for x in hist["nodes"]]
        if not hist["pageInfo"]["hasNextPage"]:
            break
        cursor = hist["pageInfo"]["endCursor"]
    return out


def analyse(u: dict) -> dict:
    repos = u["repoList"]["nodes"]
    per_repo, all_dates = [], []
    total_commits = 0
    for n in repos:
        ref = n["defaultBranchRef"]
        c = 0
        if ref and ref.get("target") and ref["target"].get("history"):
            h = ref["target"]["history"]
            c = h["totalCount"]
            got = [x["committedDate"][:10] for x in h["nodes"]]
            if c > len(got) and h["pageInfo"]["hasNextPage"]:
                got += more_dates(n["name"], h["pageInfo"]["endCursor"])
            all_dates += got
        total_commits += c
        if c:
            per_repo.append({
                "name": n["name"], "commits": c,
                "lang": (n["primaryLanguage"] or {}).get("name"),
                "stars": n["stargazerCount"],
                "releases": n["releases"]["totalCount"],
            })

    per_repo.sort(key=lambda r: -r["commits"])

    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    active = [d for d in days if d["contributionCount"] > 0]

    streak = best = 0
    for d in days:
        if d["contributionCount"] > 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0

    dow = Counter(datetime.strptime(x, "%Y-%m-%d").weekday() for x in all_dates)
    weeks_map = Counter()
    for ds in all_dates:
        dt = datetime.strptime(ds, "%Y-%m-%d").date()
        weeks_map[dt] += 1

    return {
        "since": int(u["createdAt"][:4]),
        "commits": total_commits,
        "repos": len(repos),
        "releases": sum(n["releases"]["totalCount"] for n in repos),
        "stars": sum(n["stargazerCount"] for n in repos),
        "contrib_year": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "active_days": len(active),
        "streak": best,
        "per_repo": per_repo,
        "dow": [dow.get(i, 0) for i in range(7)],
        "dates": all_dates,
        "weeks": weeks_map,
        "langs": Counter((n["primaryLanguage"] or {}).get("name") for n in repos if n["primaryLanguage"]),
    }


# ------------------------------------------------------------------ hero

def hero(d: dict) -> str:
    W, H = 880, 250
    px = 3
    n, step = 9, 88
    w_end = len(SQUID[0]) * px
    x0 = (W - ((n - 1) * step + w_end)) / 2
    row = "".join(
        f'<g transform="translate({x0 + i * step:.2f},22)">'
        + sprite(SQUID if i % 2 == 0 else CRAB, 0, 0, px, NEON)
        + f'<animateTransform attributeName="transform" type="translate" additive="sum" '
          f'values="0,0;0,5;0,0" dur="{1.8 + (i % 3) * 0.35:.2f}s" repeatCount="indefinite"/></g>'
        for i in range(n)
    )

    # stack principal como segmentos de "barra de energia"
    bar_x, bar_w = 44, W - 88
    segs, labels = [], []
    total = sum(s[3] for s in STACK)
    acc = 0.0
    for name, role, color, weight in STACK:
        w = bar_w * weight / total
        segs.append(
            f'<rect x="{bar_x + acc:.1f}" y="184" width="{max(w - 4, 6):.1f}" height="9" rx="2" fill="{color}"/>'
        )
        # rótulo centralizado sob o próprio segmento
        cx = bar_x + acc + max(w - 4, 6) / 2
        pct = round(100 * weight / total)
        labels.append(
            f'<text x="{cx:.1f}" y="207" text-anchor="middle" font-family=\'{MONO}\' '
            f'font-size="9.5" letter-spacing="1.2" fill="{color}">{name}</text>'
            f'<text x="{cx:.1f}" y="219" text-anchor="middle" font-family=\'{MONO}\' '
            f'font-size="7.5" letter-spacing="0.6" fill="{DIM}">{role}</text>'
        )
        acc += w

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ítalo Jeferson — player 1, {d['commits']} commits e stack Java, PHP, Flutter">
  <defs>
    <pattern id="s1" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.6" fill="{BLACK}" opacity="0.42"/>
    </pattern>
    <radialGradient id="v1" cx="50%" cy="44%" r="78%">
      <stop offset="0" stop-color="{BLACK}" stop-opacity="0"/>
      <stop offset="1" stop-color="{BLACK}" stop-opacity="0.9"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="{BLACK}"/>
  {row}

  <rect x="0" y="74" width="{W}" height="66" fill="{DARK}"/>
  <line x1="0" y1="74" x2="{W}" y2="74" stroke="{LINE}"/>
  <line x1="0" y1="140" x2="{W}" y2="140" stroke="{LINE}"/>

  <text x="44" y="97" font-family='{MONO}' font-size="10" letter-spacing="4" fill="{NEON}">PLAYER 1</text>
  <text x="{W-44}" y="97" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">STAGE {2026 - d['since']:02d}</text>
  <text x="44" y="126" font-family='{MONO}' font-size="31" font-weight="700" letter-spacing="6" fill="{INK}">ÍTALO JEFERSON</text>
  <text x="{W-44}" y="126" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{MUTED}">1UP {d['commits']:06d}</text>

  <text x="44" y="165" font-family='{MONO}' font-size="9.5" letter-spacing="3" fill="{DIM}">MAIN STACK</text>
  {''.join(segs)}
  {''.join(labels)}

  <rect x="{bar_x}" y="230" width="8" height="8" fill="{NEON}">
    <animate attributeName="opacity" values="1;0.15;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
  <text x="{bar_x+16}" y="238" font-family='{MONO}' font-size="9.5" letter-spacing="2.6" fill="{MUTED}">PRESS START</text>
  <text x="{W-44}" y="238" text-anchor="end" font-family='{MONO}' font-size="9.5" letter-spacing="2.6" fill="{DIM}">BASEBIT.CLOUD</text>

  <rect width="{W}" height="{H}" fill="url(#v1)"/>
  <rect width="{W}" height="{H}" fill="url(#s1)"/>
</svg>
'''


# ------------------------------------------------------------------ game

def game(d: dict) -> str:
    W, H = 880, 300
    px = 4
    score = d["commits"]

    cols, rows = 6, 3
    cell = (W - 96) / cols
    types = [SQUID, CRAB, OCTOPUS]
    invaders = "".join(
        f'<g transform="translate({48 + c * cell + (cell - len(types[r % 3][0]) * px) / 2:.1f},{78 + r * 36})">'
        f'{sprite(types[r % 3], 0, 0, px, [NEON, NEON2, MUTED][r % 3])}'
        f'<animateTransform attributeName="transform" type="translate" additive="sum" '
        f'values="0,0;0,5;0,0" dur="{2.2 + ((c + r) % 4) * 0.3:.2f}s" begin="{(c * 0.08 + r * 0.12):.2f}s" '
        f'repeatCount="indefinite"/></g>'
        for r in range(rows) for c in range(cols)
    )

    ship_y, ship_x = 210, (W - 44) / 2
    shots = "".join(
        f'<rect x="20" y="{ship_y}" width="4" height="16" fill="{WARM}" opacity="0">'
        f'<animate attributeName="y" values="{ship_y};70" dur="0.8s" begin="{b:.2f}s" '
        f'repeatCount="indefinite" keyTimes="0;1" calcMode="spline" keySplines="0.3 0 0.7 1"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" dur="0.8s" begin="{b:.2f}s" '
        f'repeatCount="indefinite" keyTimes="0;0.06;0.88;1"/></rect>'
        for b in (0.8, 2.9, 5.0, 7.1)
    )
    ship = (
        f'<g transform="translate({ship_x},{ship_y})"><g>'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0,0;-88,0;-20,0;74,0;18,0;0,0" dur="8.4s" repeatCount="indefinite"/>'
        + sprite(SHIP, 0, -8, px, INK) + shots + '</g></g>'
    )

    streak = d["streak"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cena arcade: {d['commits']} commits em {d['repos']} repositórios">
  <defs>
    <pattern id="s2" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.6" fill="{BLACK}" opacity="0.4"/>
    </pattern>
    <radialGradient id="v2" cx="50%" cy="50%" r="82%">
      <stop offset="0" stop-color="{BLACK}" stop-opacity="0"/>
      <stop offset="1" stop-color="{BLACK}" stop-opacity="0.88"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="{BLACK}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{LINE}"/>

  <text x="24" y="30" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">COMMITS</text>
  <text x="24" y="50" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{INK}">{score:06d}</text>

  <text x="{W/2}" y="30" text-anchor="middle" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">REPOS</text>
  <text x="{W/2}" y="50" text-anchor="middle" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{NEON}">{d['repos']:02d}</text>

  <text x="{W-24}" y="30" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">STREAK</text>
  <text x="{W-24}" y="50" text-anchor="end" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{INK}">{streak:02d}d</text>

  <line x1="24" y1="66" x2="{W-24}" y2="66" stroke="{LINE}" opacity="0.8"/>
  {invaders}
  {ship}

  <line x1="24" y1="276" x2="{W-24}" y2="276" stroke="{LINE}"/>
  <rect x="24" y="276" width="{W-48}" height="2" fill="{NEON}" opacity="0.3"/>
  <text x="24" y="294" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{DIM}">{d['releases']} RELEASES · {d['contrib_year']} CONTRIBUIÇÕES/12M</text>
  <text x="{W/2}" y="294" text-anchor="middle" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{DIM}">CREDIT 01</text>
  <text x="{W-24}" y="294" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{NEON}">
    <a href="{GAME_URL}">JOGAR ▸</a>
  </text>

  <rect width="{W}" height="{H}" fill="url(#v2)"/>
  <rect width="{W}" height="{H}" fill="url(#s2)"/>
</svg>
'''


# ------------------------------------------------------------------ leaderboard

def leaderboard(d: dict) -> str:
    rows = d["per_repo"][:6]
    W = 424
    pad = 22
    top = 74
    row_h = 34
    H = top + len(rows) * row_h + 34
    mx = max(r["commits"] for r in rows) or 1
    shown = sum(r["commits"] for r in rows)

    items = []
    for i, r in enumerate(rows):
        y = top + i * row_h
        frac = r["commits"] / mx
        barw = 150
        fill = barw * frac
        items.append(
            f'<text x="{pad}" y="{y}" font-family=\'{MONO}\' font-size="10" '
            f'letter-spacing="1.5" fill="{NEON if i == 0 else MUTED}">{i+1:02d}</text>'
            f'<text x="{pad+26}" y="{y}" font-family=\'{MONO}\' font-size="10.5" fill="{INK}">{r["name"][:17]}</text>'
            f'<rect x="{pad+158}" y="{y-7}" width="{barw}" height="7" fill="{LINE}"/>'
            f'<rect x="{pad+158}" y="{y-7}" width="{fill:.1f}" height="7" fill="{NEON if i == 0 else NEON2}" opacity="{1 if i == 0 else 0.65}"/>'
            f'<text x="{W-pad}" y="{y}" text-anchor="end" font-family=\'{MONO}\' font-size="10.5" font-weight="700" fill="{MUTED}">{r["commits"]:03d}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ranking de repositórios por commits">
  <defs>
    <pattern id="s3" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.5" fill="{BLACK}" opacity="0.4"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{H}" fill="{BLACK}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="{DARK}" stroke="{LINE}"/>

  <text x="{pad}" y="30" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{NEON}">LEADERBOARD</text>
  <text x="{W-pad}" y="30" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="0" fill="{MUTED}">COMMITS</text>
  <line x1="{pad}" y1="40" x2="{W-pad}" y2="40" stroke="{LINE}"/>
  <text x="{pad}" y="60" font-family='{MONO}' font-size="9" letter-spacing="1.6" fill="{MUTED}">TOP {len(rows)} DE {d['repos']} REPOS · {shown} DE {d['commits']} COMMITS</text>

  {''.join(items)}

  <line x1="{pad}" y1="{H-22}" x2="{W-pad}" y2="{H-22}" stroke="{LINE}" opacity="0.7"/>
  <text x="{pad}" y="{H-8}" font-family='{MONO}' font-size="9" letter-spacing="1.6" fill="{DIM}">branch principal · só commits</text>

  <rect width="{W}" height="{H}" fill="url(#s3)"/>
</svg>
'''


# ------------------------------------------------------------------ rhythm

def rhythm(d: dict) -> str:
    """Timeline mensal completo + perfil por dia da semana."""
    W = 424
    pad = 22
    inner = W - 2 * pad

    months = Counter(ds[:7] for ds in d["dates"])
    first, last = min(months), max(months)
    y0, m0 = int(first[:4]), int(first[5:7])
    y1, m1 = int(last[:4]), int(last[5:7])
    span = (y1 - y0) * 12 + (m1 - m0) + 1
    seq = []
    for i in range(span):
        yy, mm = divmod(m0 - 1 + i, 12)
        seq.append((f"{y0 + yy}-{mm + 1:02d}", months.get(f"{y0 + yy}-{mm + 1:02d}", 0)))

    mx = max(v for _, v in seq) or 1
    gap = 1.6
    bar_w = max(3.0, (inner - (span - 1) * gap) / span)

    # bandas verticais fixas — sem sobreposição entre seções
    base_y = 152
    max_h = 76
    year_y = base_y + 14
    wk_title = 200
    wk_top = 216
    wk_h = 28
    wk_base = wk_top + wk_h
    H = wk_base + 30

    bars, years = [], []
    seen = None
    for i, (key, v) in enumerate(seq):
        x = pad + i * (bar_w + gap)
        h = max(1.5, max_h * v / mx)
        hot = v == mx
        bars.append(
            f'<rect x="{x:.1f}" y="{base_y - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'fill="{WARM if hot else NEON}" opacity="{1 if hot else 0.7}"/>'
        )
        if key[:4] != seen:
            seen = key[:4]
            years.append(
                f'<text x="{x:.1f}" y="{year_y}" font-family=\'{MONO}\' font-size="8.5" '
                f'letter-spacing="1" fill="{MUTED}">{seen}</text>'
            )

    avg = sum(v for _, v in seq) / span
    avg_y = base_y - max_h * avg / mx
    avg_lbl = f"MÉDIA {avg:.0f}/MÊS"

    dow = d["dow"]
    dmx = max(dow) or 1
    names = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
    col_w = inner / 7
    bw = col_w - 12
    wk = []
    for i, v in enumerate(dow):
        cx = pad + i * col_w
        bh = max(2.0, wk_h * v / dmx)
        hot = v == dmx
        wk.append(
            f'<rect x="{cx:.1f}" y="{wk_base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'fill="{WARM if hot else NEON2}" opacity="{1 if hot else 0.55}"/>'
            f'<text x="{cx + bw / 2:.1f}" y="{wk_base + 12}" text-anchor="middle" '
            f'font-family=\'{MONO}\' font-size="8" letter-spacing="0.5" fill="{MUTED if hot else DIM}">{names[i]}</text>'
            f'<text x="{cx + bw / 2:.1f}" y="{wk_base + 24}" text-anchor="middle" '
            f'font-family=\'{MONO}\' font-size="8.5" fill="{NEON if hot else MUTED}">{v:02d}</text>'
        )

    peak = max(seq, key=lambda kv: kv[1])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Frequência: {d['commits']} commits distribuídos em {span} meses e por dia da semana">
  <defs>
    <pattern id="s4" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.5" fill="{BLACK}" opacity="0.4"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{H}" fill="{BLACK}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="{DARK}" stroke="{LINE}"/>

  <text x="{pad}" y="30" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{NEON}">FREQUÊNCIA</text>
  <text x="{W-pad}" y="30" text-anchor="end" font-family='{MONO}' font-size="9.5" letter-spacing="1.2" fill="{MUTED}">{span} MESES · {d['commits']} COMMITS</text>
  <line x1="{pad}" y1="40" x2="{W-pad}" y2="40" stroke="{LINE}"/>
  <text x="{pad}" y="60" font-family='{MONO}' font-size="9" letter-spacing="1.8" fill="{MUTED}">COMMITS POR MÊS</text>
  <text x="{W-pad}" y="60" text-anchor="end" font-family='{MONO}' font-size="9" letter-spacing="1.2" fill="{WARM}">PICO {peak[0][5:]}/{peak[0][:4]} · {peak[1]}</text>

  <line x1="{pad}" y1="{base_y}" x2="{W-pad}" y2="{base_y}" stroke="{LINE}"/>
  <line x1="{pad}" y1="{avg_y:.1f}" x2="{W-pad}" y2="{avg_y:.1f}" stroke="{DIM}" stroke-dasharray="2 3" opacity="0.55"/>
  <text x="{W-pad}" y="{avg_y - 5:.1f}" text-anchor="end" font-family='{MONO}' font-size="7.5" letter-spacing="0.8" fill="{DIM}">{avg_lbl}</text>
  {''.join(bars)}
  {''.join(years)}

  <text x="{pad}" y="{wk_title}" font-family='{MONO}' font-size="9" letter-spacing="1.8" fill="{MUTED}">POR DIA DA SEMANA</text>
  <line x1="{pad}" y1="{wk_base}" x2="{W-pad}" y2="{wk_base}" stroke="{LINE}"/>
  {''.join(wk)}

  <rect width="{W}" height="{H}" fill="url(#s4)"/>
</svg>
'''


# ------------------------------------------------------------------ botões

BUTTONS = [
    ("linkedin",  "LINKEDIN",  "CONVERSAR", "#74C0F5", 300),
    ("portfolio", "PORTFOLIO", "BASEBIT.CLOUD",   "#3FD99A", 300),
    ("email",     "E-MAIL",    "MANDAR UM OI",    "#F9B54A", 300),
]


def button(label: str, sub: str, color: str, w: int) -> str:
    """Botão de fliperama. Tipo grande o suficiente para o README mobile:
    a 100px de largura o rótulo ainda fica com ~12px."""
    H = 112
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" role="img" aria-label="{label} — {sub}">
  <rect x="2" y="5" width="{w-4}" height="{H-10}" rx="9" fill="{color}" opacity="0.10"/>
  <rect x="3" y="11" width="{w-6}" height="{H-17}" rx="7" fill="{color}" opacity="0.45"/>
  <rect x="3" y="3" width="{w-6}" height="{H-17}" rx="7" fill="{DARK}" stroke="{color}" stroke-width="2.2"/>
  <rect x="11" y="11" width="{w-22}" height="{H-33}" rx="3" fill="none" stroke="{color}" stroke-width="1" opacity="0.28"/>
  <circle cx="27" cy="44" r="5" fill="{color}">
    <animate attributeName="opacity" values="1;0.15;1" dur="1.5s" repeatCount="indefinite"/>
  </circle>
  <text x="43" y="50" font-family=\'{MONO}\' font-size="29" font-weight="700" letter-spacing="0.6" fill="{color}">{label}</text>
  <text x="43.5" y="92" font-family=\'{MONO}\' font-size="23" letter-spacing="0.1" fill="{INK}" opacity="0.82">{sub}</text>
  <path d="M{w-42} 41 L{w-28} 52 L{w-42} 63" fill="none" stroke="{color}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''


def compose(left_svg: str, right_svg: str, stack: bool = False) -> str:
    """Junta os dois cards. Lado a lado no desktop; empilhados no mobile,
    onde lado a lado reduziria a fonte a ~3px."""
    import re

    def body(svg: str):
        inner = svg[svg.index(">") + 1: svg.rindex("</svg>")]
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        return inner, int(vb.group(1)), int(vb.group(2))

    li, lw, lh = body(left_svg)
    ri, rw, rh = body(right_svg)

    if stack:
        W = 440

        def full(inner: str, vw: int, vh: int, y: float):
            h = W * vh / vw
            return (f'<svg x="0" y="{y:.1f}" width="{W}" height="{h:.1f}" '
                    f'viewBox="0 0 {vw} {vh}">{inner}</svg>'), h

        l, lhh = full(li, lw, lh, 0)
        r, rhh = full(ri, rw, rh, lhh + 8)
        H = lhh + rhh + 8
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" role="img" aria-label="Métricas por repositório e frequência de commits">
  <rect width="{W}" height="{H:.0f}" fill="{BLACK}"/>
  {l}
  {r}
</svg>
'''

    W, gap = 880, 10
    col = (W - gap) / 2
    H = max(col * lh / lw, col * rh / rw)

    def box(inner: str, vw: int, vh: int, x: float) -> str:
        h = col * vh / vw
        return (f'<svg x="{x:.1f}" y="0" width="{col:.1f}" height="{h:.1f}" '
                f'viewBox="0 0 {vw} {vh}" preserveAspectRatio="xMinYMin meet">{inner}</svg>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" role="img" aria-label="Métricas: ranking de repositórios por commits e frequência de commits">
  <rect width="{W}" height="{H:.0f}" fill="{BLACK}"/>
  {box(li, lw, lh, 0)}
  {box(ri, rw, rh, col + gap)}
</svg>
'''


def main() -> None:
    d = analyse(fetch())
    os.makedirs(OUT, exist_ok=True)

    svgs = {"hero": hero(d), "game": game(d),
            "leaderboard": leaderboard(d), "rhythm": rhythm(d)}
    svgs["stats"] = compose(svgs["leaderboard"], svgs["rhythm"])
    svgs["stats-mobile"] = compose(svgs["leaderboard"], svgs["rhythm"], stack=True)
    for key, label, sub, color, w in BUTTONS:
        svgs[f"btn-{key}"] = button(label, sub, color, w)

    for name, svg in svgs.items():
        path = os.path.join(OUT, f"{name}.svg")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(svg)
        os.replace(tmp, path)

    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump({k: v for k, v in d.items() if k not in ("dates", "weeks")},
                  f, ensure_ascii=False, indent=2, default=str)

    print(f"ok · {d['commits']} commits · {d['repos']} repos · streak {d['streak']}d "
          f"· top {d['per_repo'][0]['name']} ({d['per_repo'][0]['commits']}) "
          f"· {len(svgs)} svgs")


if __name__ == "__main__":
    main()
