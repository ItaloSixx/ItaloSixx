#!/usr/bin/env python3
"""SVGs do perfil — arcade. Fundo preto, sprites em pixel grid, SMIL.

assets/hero.svg   marquise de fliperama
assets/game.svg   cena de jogo em attract mode (HUD com dados reais)

Sem dependências externas. Uso: GH_TOKEN=... python scripts/assets.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter

USER = os.environ.get("PROFILE_USER", "ItaloSixx")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'

BLACK = "#000000"
DARK = "#0A0A0C"
LINE = "#232329"
INK = "#FFFFFF"
MUTED = "#8A8A96"
DIM = "#565663"
NEON = "#3DF5A8"
NEON2 = "#5AC8FF"
WARM = "#FFB84D"
RED = "#FF4D6A"
GAME_URL = "https://italosixx.github.io/ItaloSixx/"

# --------------------------------------------------------------- sprites
# 8-bit, simétricos, desenhados à mão (1 unidade = 1 pixel)

CRAB = [                      # 11x8 — clássico "crab"
    "..X.....X..",
    "...X...X...",
    "..XXXXXXX..",
    ".XX.XXX.XX.",
    "XXXXXXXXXXX",
    "X.XXXXXXX.X",
    "X.X.....X.X",
    "...XX.XX...",
]

SQUID = [                     # 8x8 — "squid"
    "...XX...",
    "..XXXX..",
    ".XXXXXX.",
    "XX.XX.XX",
    "XXXXXXXX",
    "..X..X..",
    ".X.XX.X.",
    "X.X..X.X",
]

OCTOPUS = [                   # 12x8 — "octopus"
    "....XXXX....",
    ".XXXXXXXXXX.",
    "XXXXXXXXXXXX",
    "XXX..XX..XXX",
    "XXXXXXXXXXXX",
    "...XX..XX...",
    "..XX.XX.XX..",
    "XX........XX",
]

SHIP = [                      # 11x8
    ".....X.....",
    "....XXX....",
    "....XXX....",
    ".XXXXXXXXX.",
    "XXXXXXXXXXX",
    "XXXXXXXXXXX",
    "XX.XXXXX.XX",
    "X...X.X...X",
]

BOOM = [                      # 7x7
    "..X...X",
    ".X.X.X.",
    "..XXX..",
    "XXXXXXX",
    "..XXX..",
    ".X.X.X.",
    "X...X..",
]


def sprite(rows, x: float, y: float, px: float, color: str) -> str:
    """Sprite de caracteres -> retângulos exatos (sem antialias)."""
    out = []
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch == "X":
                out.append(f'<rect x="{x + rx * px:g}" y="{y + ry * px:g}" width="{px:g}" height="{px:g}"/>')
    return f'<g fill="{color}" shape-rendering="crispEdges">{"".join(out)}</g>'


def _cell_sprite(rows, cell_x: float, cell_w: float, y: float, px: float,
                 color: str, extra: str = "") -> str:
    """Centraliza um sprite dentro de uma célula de largura fixa."""
    w = len(rows[0]) * px
    x = cell_x + (cell_w - w) / 2
    return f'<g transform="translate({x:.2f},{y:g})">{sprite(rows, 0, 0, px, color)}{extra}</g>'


# --------------------------------------------------------------- API

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repoList: repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes { primaryLanguage { name } releases { totalCount } }
    }
  }
}
"""


def collect() -> dict:
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
    u = payload["data"]["user"]
    repos = u["repoList"]["nodes"]
    return {
        "since": int(u["createdAt"][:4]),
        "repos": len(repos),
        "releases": sum(n["releases"]["totalCount"] for n in repos),
        "langs": Counter(n["primaryLanguage"]["name"] for n in repos if n["primaryLanguage"]),
    }


# --------------------------------------------------------------- hero

def hero(d: dict) -> str:
    W, H = 880, 216
    px = 3
    n, step = 9, 88
    w_end = len(SQUID[0]) * px        # extremidades iguais => margens iguais
    x0 = (W - ((n - 1) * step + w_end)) / 2
    row = "".join(
        f'<g transform="translate({x0 + i * step:.2f},26)">'
        + sprite(SQUID if i % 2 == 0 else CRAB, 0, 0, px, NEON)
        + f'<animateTransform attributeName="transform" type="translate" additive="sum" '
          f'values="0,0;0,5;0,0" dur="{1.8 + (i % 3) * 0.35:.2f}s" repeatCount="indefinite"/></g>'
        for i in range(n)
    )
    stars = "".join(
        f'<rect x="{(i * 197) % (W - 30) + 15}" y="{(i * 61) % 78 + 6}" width="2" height="2" fill="{INK}" opacity="0.2"/>'
        for i in range(22)
    )
    lv = 2026 - d["since"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ítalo Jeferson — player 1">
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
  {stars}
  {row}

  <rect x="0" y="80" width="{W}" height="66" fill="{DARK}"/>
  <line x1="0" y1="80" x2="{W}" y2="80" stroke="{LINE}"/>
  <line x1="0" y1="146" x2="{W}" y2="146" stroke="{LINE}"/>

  <text x="44" y="103" font-family='{MONO}' font-size="10" letter-spacing="4" fill="{NEON}">PLAYER 1</text>
  <text x="{W-44}" y="103" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">STAGE {lv:02d}</text>
  <text x="44" y="132" font-family='{MONO}' font-size="31" font-weight="700" letter-spacing="6" fill="{INK}">ÍTALO JEFERSON</text>
  <text x="{W-44}" y="132" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">
    <tspan x="{W-44}" dy="0">1UP {d['repos']:05d}</tspan>
  </text>

  <g>
    <rect x="44" y="158" width="9" height="9" fill="{NEON}">
      <animate attributeName="opacity" values="1;0.1;1" dur="1.05s" repeatCount="indefinite"/>
    </rect>
    <text x="63" y="167" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">PRESS START</text>
    <text x="{W-44}" y="167" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{DIM}">BASEBIT.CLOUD</text>
  </g>

  <rect width="{W}" height="{H}" fill="url(#v1)"/>
  <rect width="{W}" height="{H}" fill="url(#s1)"/>
</svg>
'''


# --------------------------------------------------------------- cena de jogo

def game(d: dict) -> str:
    W, H = 880, 300
    px = 4
    lv = 2026 - d["since"]
    top_lang = d["langs"].most_common(1)[0][0] if d["langs"] else "—"
    score = d["repos"] * 137 + d["releases"] * 50
    hi = score + 12500

    stars = "".join(
        f'<rect x="{(i * 131) % (W - 20) + 10}" y="{(i * 79) % (H - 80) + 56}" width="2" height="2" '
        f'fill="{INK}" opacity="0.2"><animate attributeName="opacity" values="0.2;0.04;0.2" '
        f'dur="{2 + (i % 5) * 0.7:.1f}s" repeatCount="indefinite"/></rect>'
        for i in range(30)
    )

    # formação em grade regular de 6 colunas
    cols, cell = 6, (W - 96) / 6
    types = [SQUID, CRAB, OCTOPUS]
    # cada alien pisca no instante em que o tiro chega nele
    hit_at = {1: 0.072, 3: 0.322, 0: 0.572, 5: 0.822}
    invaders = "".join(
        _cell_sprite(types[i % 3], 48 + i * cell, cell, 84, px,
                     NEON if i % 2 else NEON2,
                     f'<animateTransform attributeName="transform" type="translate" additive="sum" '
                     f'values="0,0;0,6;0,0" dur="2.4s" begin="{i * 0.1:.2f}s" repeatCount="indefinite"/>'
                     + (f'<animate attributeName="opacity" values="1;1;0.1;1;1" dur="8.4s" '
                        f'repeatCount="indefinite" keyTimes="0;{hit_at[i]:.3f};{hit_at[i]+0.022:.3f};'
                        f'{hit_at[i]+0.10:.3f};1"/>' if i in hit_at else ""))
        for i in range(cols)
    )

    # nave + tiros no mesmo grupo: o disparo sai sempre do canhão
    ship_y = 236
    ship_x = (W - 44) / 2
    shots = "".join(
        f'<rect x="20" y="{ship_y}" width="4" height="16" fill="{WARM}" opacity="0">'
        f'<animate attributeName="y" values="{ship_y};86" dur="0.8s" begin="{b:.2f}s" '
        f'repeatCount="indefinite" keyTimes="0;1" calcMode="spline" keySplines="0.3 0 0.7 1"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" dur="0.8s" begin="{b:.2f}s" '
        f'repeatCount="indefinite" keyTimes="0;0.06;0.88;1"/></rect>'
        for b in (0.8, 2.9, 5.0, 7.1)
    )
    ship = (
        f'<g transform="translate({ship_x},{ship_y})">'
        '<g>'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0,0;-88,0;-20,0;74,0;18,0;0,0" dur="8.4s" repeatCount="indefinite"/>'
        + sprite(SHIP, 0, -8, px, INK)
        + shots
        + '</g></g>'
    )


    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cena de jogo arcade com {d['repos']} repositórios e {d['releases']} releases">
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
  {stars}
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{LINE}"/>

  <text x="24" y="30" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">SCORE</text>
  <text x="24" y="48" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{INK}">{score:06d}</text>

  <text x="{W/2}" y="30" text-anchor="middle" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">HI-SCORE</text>
  <text x="{W/2}" y="48" text-anchor="middle" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{NEON}">{hi:06d}</text>

  <text x="{W-24}" y="30" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="3" fill="{MUTED}">STAGE</text>
  <text x="{W-24}" y="48" text-anchor="end" font-family='{MONO}' font-size="15" font-weight="700" letter-spacing="2" fill="{INK}">{lv:02d}</text>

  <line x1="24" y1="66" x2="{W-24}" y2="66" stroke="{LINE}" opacity="0.8"/>

  {invaders}
  {ship}

  <line x1="24" y1="276" x2="{W-24}" y2="276" stroke="{LINE}"/>
  <rect x="24" y="276" width="{W-48}" height="2" fill="{NEON}" opacity="0.3"/>
  <text x="24" y="294" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{DIM}">MAIN · {top_lang.upper()}</text>
  <text x="{W/2}" y="294" text-anchor="middle" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{DIM}">CREDIT 01</text>
  <text x="{W-24}" y="294" text-anchor="end" font-family='{MONO}' font-size="10" letter-spacing="2" fill="{NEON}">
    <a href="{GAME_URL}"><tspan fill="{NEON}">JOGAR ▸</tspan></a>
  </text>

  <rect width="{W}" height="{H}" fill="url(#v2)"/>
  <rect width="{W}" height="{H}" fill="url(#s2)"/>
</svg>
'''


def main() -> None:
    d = collect()
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("hero", hero), ("game", game)):
        path = os.path.join(OUT, f"{name}.svg")
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.write(fn(d))
        os.replace(tmp, path)
    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump({**d, "langs": dict(d["langs"])}, f, ensure_ascii=False, indent=2)
    print(f"ok · {d['repos']} repos · {d['releases']} releases · lv {2026 - d['since']}")


if __name__ == "__main__":
    main()
