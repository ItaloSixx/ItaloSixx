#!/usr/bin/env python3
"""Gera os SVGs do perfil (hero + telemetria) direto da API do GitHub.

Sem serviços de terceiros: os cards são estáticos, versionados no repo e
regenerados pelo workflow .github/workflows/assets.yml.
"""
from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter

USER = os.environ.get("PROFILE_USER", "ItaloSixx")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

THEMES = {
    "dark": {
        "bg": "#080C11", "panel": "#0C121A", "grid": "#131C26", "line": "#22303F",
        "ink": "#E9F1F8", "muted": "#8FA3B6", "dim": "#66798C",
        "accent": "#3DF5A8", "second": "#4FC8FF",
    },
    "light": {
        "bg": "#FFFFFF", "panel": "#F5F8FB", "grid": "#E4EBF2", "line": "#D2DDE7",
        "ink": "#0B1620", "muted": "#4E6173", "dim": "#5C6E80",
        "accent": "#067A57", "second": "#0B7FB0",
    },
}

LANG_COLORS = {
    "Java": "#b07219", "PHP": "#6B78C4", "C": "#8A9299", "Python": "#3572A5",
    "Dart": "#00B4AB", "TypeScript": "#3178c6", "C++": "#f34b7d",
    "Jupyter Notebook": "#DA5B0B", "Kotlin": "#A97BFF", "JavaScript": "#e0c33a",
}


def gh(query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-assets",
        },
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL: {payload['errors']}")
    return payload["data"]


QUERY = """
query($login: String!) {
  user(login: $login) {
    name followers { totalCount }
    repoList: repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        name stargazerCount
        primaryLanguage { name }
        releases { totalCount }
      }
    }
  }
}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def collect() -> dict:
    u = gh(QUERY, {"login": USER})["user"]
    repos = u["repoList"]["nodes"]
    langs = Counter(n["primaryLanguage"]["name"] for n in repos if n["primaryLanguage"])
    return {
        "followers": u["followers"]["totalCount"],
        "repos": len(repos),
        "stars": sum(n["stargazerCount"] for n in repos),
        "releases": sum(n["releases"]["totalCount"] for n in repos),
        "with_lang": sum(langs.values()),
        "langs": langs,
    }


def compact_langs(langs: Counter, keep: int = 5) -> list[tuple[str, int]]:
    """Top N + 'Outros', para a legenda caber em duas colunas de três linhas."""
    top = langs.most_common(keep)
    rest = sum(v for _, v in langs.most_common()[keep:])
    out = list(top)
    if rest:
        out.append(("Outros", rest))
    return out


# --------------------------------------------------------------------- hero

def hero(t: dict, d: dict) -> str:
    W, H = 880, 250
    base = 196  # linha de base do ECG
    beats, x = [], 30
    while x < W - 40:
        beats.append(
            f"M {x} {base} h 12 l 3 -5 l 3 9 l 4 -22 l 5 30 l 5 -12 l 4 0 h 14"
            f" l 3 -3 l 2 6 l 3 -15 l 4 21 l 4 -9 l 3 0"
        )
        x += 104
    ecg = " ".join(beats)
    dots = "".join(
        f'<circle cx="{cx}" cy="{base}" r="2.4" fill="{t["accent"]}" opacity="0.5"/>'
        for cx in range(30, W - 40, 104)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ítalo Jeferson — software para saúde pública e sistemas embarcados">
  <defs>
    <pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0H0V40" fill="none" stroke="{t['grid']}" stroke-width="1"/>
    </pattern>
    <linearGradient id="top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['bg']}" stop-opacity="0"/>
      <stop offset="0.55" stop-color="{t['bg']}" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="ecg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['accent']}" stop-opacity="0.2"/>
      <stop offset="0.4" stop-color="{t['accent']}" stop-opacity="1"/>
      <stop offset="1" stop-color="{t['second']}" stop-opacity="0.85"/>
    </linearGradient>
    <clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#c)">
    <rect width="{W}" height="{H}" fill="{t['bg']}"/>
    <rect width="{W}" height="{H}" fill="url(#g)"/>
    <rect width="{W}" height="{H}" fill="url(#top)" opacity="0.8"/>

    <circle cx="32" cy="33" r="4" fill="{t['accent']}">
      <animate attributeName="opacity" values="1;0.2;1" dur="2.6s" repeatCount="indefinite"/>
    </circle>
    <text x="46" y="37" font-family='{MONO}' font-size="11" letter-spacing="2" fill="{t['muted']}">DISPONÍVEL PARA PROJETOS</text>
    <text x="{W-32}" y="37" text-anchor="end" font-family='{MONO}' font-size="11" letter-spacing="1.4" fill="{t['muted']}">IF BAIANO · GUANAMBI/BA</text>
    <line x1="32" y1="52" x2="{W-32}" y2="52" stroke="{t['line']}" stroke-width="1"/>

    <text x="32" y="102" font-family='{MONO}' font-size="38" font-weight="700" fill="{t['ink']}" letter-spacing="-0.8">ÍTALO JEFERSON</text>
    <text x="32" y="130" font-family='{MONO}' font-size="14" fill="{t['accent']}">software para saúde pública e sistemas embarcados</text>
    <text x="32" y="153" font-family='{MONO}' font-size="12" fill="{t['muted']}">Java · PHP/Laravel · Flutter · ESP32 · Python — do firmware à API</text>

    <g>
      <path d="{ecg}" fill="none" stroke="{t['line']}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="{ecg}" fill="none" stroke="url(#ecg)" stroke-width="1.8" stroke-linecap="round"
            stroke-dasharray="200 {W}" stroke-dashoffset="0">
        <animate attributeName="stroke-dashoffset" from="200" to="-{W + 200}" dur="8s" repeatCount="indefinite"/>
      </path>
      {dots}
    </g>

    <line x1="32" y1="{H-34}" x2="{W-32}" y2="{H-34}" stroke="{t['line']}" stroke-width="1" opacity="0.7"/>
    <text x="32" y="{H-14}" font-family='{MONO}' font-size="10" letter-spacing="1.6" fill="{t['dim']}">github.com/{USER}</text>
    <text x="{W-32}" y="{H-14}" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="1.6" fill="{t['dim']}">{d['repos']} REPOSITÓRIOS · {d['releases']} RELEASES · {d['followers']} FOLLOWERS</text>
  </g>
</svg>
'''


# ---------------------------------------------------------------- telemetria

def telemetry(t: dict, d: dict) -> str:
    W = 880
    pad = 32
    series = compact_langs(d["langs"])
    total = sum(v for _, v in series) or 1

    kpis = [
        ("PROJETOS PÚBLICOS", d["repos"]),
        ("RELEASES", d["releases"]),
        ("LINGUAGENS", len(d["langs"])),
        ("FOLLOWERS", d["followers"]),
    ]

    y_head, y_rule1 = 38, 54
    y_kpi_label, y_kpi_value, y_rule2 = 82, 124, 148
    y_stack_title, y_bar = 172, 186
    legend_top, row_h = 216, 26
    rows = (len(series) + 1) // 2
    y_footer = legend_top + (rows - 1) * row_h + 34
    H = y_footer + 16

    cell = (W - 2 * pad) / len(kpis)
    cells = []
    for i, (label, value) in enumerate(kpis):
        cx = pad + i * cell
        if i:
            cells.append(
                f'<line x1="{cx-20:.1f}" y1="{y_kpi_label-14}" x2="{cx-20:.1f}" '
                f'y2="{y_kpi_value+8}" stroke="{t["line"]}" stroke-width="1"/>'
            )
        cells.append(
            f'<text x="{cx:.1f}" y="{y_kpi_label}" font-family=\'{MONO}\' font-size="9.5" '
            f'letter-spacing="1.8" fill="{t["dim"]}">{label}</text>'
            f'<text x="{cx:.1f}" y="{y_kpi_value}" font-family=\'{MONO}\' font-size="32" '
            f'font-weight="700" fill="{t["accent"]}">{value}</text>'
        )

    bar_w = W - 2 * pad
    gap = 3
    usable = bar_w - gap * (len(series) - 1)
    segs, acc = [], 0.0
    for name, n in series:
        w = max(usable * n / total, 8)
        segs.append(
            f'<rect x="{pad + acc:.1f}" y="{y_bar}" width="{w:.1f}" height="9" rx="2" '
            f'fill="{LANG_COLORS.get(name, t["dim"])}"/>'
        )
        acc += w + gap

    col_w = (W - 2 * pad) / 2
    leg = []
    for i, (name, n) in enumerate(series):
        col, row = divmod(i, rows)
        lx = pad + col * col_w
        ly = legend_top + row * row_h
        val_x = lx + 150
        leg.append(
            f'<circle cx="{lx+5}" cy="{ly-4}" r="4" fill="{LANG_COLORS.get(name, t["dim"])}"/>'
            f'<text x="{lx+17}" y="{ly}" font-family=\'{MONO}\' font-size="11.5" fill="{t["ink"]}">{esc(name)}</text>'
            f'<text x="{val_x:.1f}" y="{ly}" text-anchor="end" font-family=\'{MONO}\' font-size="11" fill="{t["dim"]}">{n:02d}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Telemetria do perfil: {d['repos']} repositórios públicos, {d['releases']} releases, distribuição de linguagens">
  <defs>
    <pattern id="g2" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0H0V40" fill="none" stroke="{t['grid']}" stroke-width="1"/>
    </pattern>
    <clipPath id="c2"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#c2)">
    <rect width="{W}" height="{H}" fill="{t['panel']}"/>
    <rect width="{W}" height="{H}" fill="url(#g2)" opacity="0.5"/>
    <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{t['line']}"/>

    <text x="{pad}" y="{y_head}" font-family='{MONO}' font-size="10.5" letter-spacing="2.4" fill="{t['muted']}">TELEMETRIA DO PERFIL</text>
    <text x="{W-pad}" y="{y_head}" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="1" fill="{t['dim']}">dados públicos via API do GitHub</text>
    <line x1="{pad}" y1="{y_rule1}" x2="{W-pad}" y2="{y_rule1}" stroke="{t['line']}" stroke-width="1"/>

    {''.join(cells)}
    <line x1="{pad}" y1="{y_rule2}" x2="{W-pad}" y2="{y_rule2}" stroke="{t['line']}" stroke-width="1"/>

    <text x="{pad}" y="{y_stack_title}" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{t['dim']}">STACK · LINGUAGEM PRINCIPAL · {d['with_lang']} DE {d['repos']} REPOSITÓRIOS</text>
    {''.join(segs)}
    {''.join(leg)}

    <line x1="{pad}" y1="{y_footer-14}" x2="{W-pad}" y2="{y_footer-14}" stroke="{t['line']}" stroke-width="1" opacity="0.6"/>
    <text x="{pad}" y="{y_footer}" font-family='{MONO}' font-size="9" letter-spacing="1.2" fill="{t['dim']}">atualizado automaticamente por GitHub Actions</text>
  </g>
</svg>
'''


def main() -> None:
    d = collect()
    os.makedirs(OUT, exist_ok=True)
    for mode, theme in THEMES.items():
        for name, fn in (("hero", hero), ("telemetry", telemetry)):
            path = os.path.join(OUT, f"{name}-{mode}.svg")
            tmp = path + ".tmp"
            with open(tmp, "w") as f:          # escrita atômica: falha não corrompe o card
                f.write(fn(theme, d))
            os.replace(tmp, path)
    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump({**d, "langs": dict(d["langs"])}, f, ensure_ascii=False, indent=2)
    print(f"ok · {d['repos']} repos · {d['releases']} releases · {dict(d['langs'].most_common(6))}")


if __name__ == "__main__":
    main()
