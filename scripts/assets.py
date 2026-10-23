#!/usr/bin/env python3
"""Perfil de Ítalo Jeferson — fliperama desenhado, não estilizado.

Regras que este arquivo respeita (craft floor):
  * alfabeto bitmap autoral (glyphs.py), não fonte do sistema;
  * sem kicker acima de título, sem trio de métricas grandes, sem números
    decorativos: todo número aqui é um fato do repositório;
  * a formação de invaders É o dado — uma coluna por mês, altura = commits;
  * um único momento de movimento, o resto parado.

Uso: GH_TOKEN=... python3 scripts/assets.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter

import glyphs as G

USER = os.environ.get("PROFILE_USER", "ItaloSixx")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

GROUND = "#08090B"
INK = "#E8E8E6"
DIM = "#7C7F86"
PHOS = "#4BE38C"
AMBER = "#F0B24A"
GAME_URL = "https://italosixx.github.io/ItaloSixx/"
LINKEDIN = "https://www.linkedin.com/in/italo-jeferson-32778726b/"
SITE = "https://italo.basebit.cloud"
MAIL = "mailto:italojefer55@gmail.com"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
    repoList: repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        name stargazerCount primaryLanguage { name } releases { totalCount }
        defaultBranchRef { target { ... on Commit { history(first: 100) {
          totalCount pageInfo { hasNextPage endCursor } nodes { committedDate }
        } } } }
      }
    }
  }
}
"""

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
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-assets"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]


def more_dates(name: str, cursor: str) -> list:
    """history(first:100) devolve no máximo 100 datas; pagina o resto."""
    out = []
    for _ in range(20):
        repo = gql(PAGE_QUERY, {"login": USER, "name": name, "cursor": cursor})["repository"]
        hist = ((repo["defaultBranchRef"] or {}).get("target") or {}).get("history")
        if not hist:
            break
        out += [x["committedDate"][:10] for x in hist["nodes"]]
        if not hist["pageInfo"]["hasNextPage"]:
            break
        cursor = hist["pageInfo"]["endCursor"]
    return out


def fetch() -> dict:
    return gql(QUERY, {"login": USER})


def analyse(u: dict) -> dict:
    repos = u["repoList"]["nodes"]
    per_repo, dates = [], []
    total = 0
    for n in repos:
        ref = n["defaultBranchRef"]
        c = 0
        if ref and ref.get("target") and ref["target"].get("history"):
            h = ref["target"]["history"]
            c = h["totalCount"]
            got = [x["committedDate"][:10] for x in h["nodes"]]
            if c > len(got) and h["pageInfo"]["hasNextPage"]:
                got += more_dates(n["name"], h["pageInfo"]["endCursor"])
            dates += got
        total += c
        if c:
            per_repo.append({"name": n["name"], "commits": c,
                             "lang": (n["primaryLanguage"] or {}).get("name"),
                             "stars": n["stargazerCount"],
                             "releases": n["releases"]["totalCount"]})
    per_repo.sort(key=lambda r: -r["commits"])

    months = Counter(d[:7] for d in dates)
    langs = Counter((n["primaryLanguage"] or {}).get("name")
                    for n in repos if n["primaryLanguage"])
    return {
        "since": int(u["createdAt"][:4]),
        "commits": total,
        "repos": len(repos),
        "releases": sum(n["releases"]["totalCount"] for n in repos),
        "stars": sum(n["stargazerCount"] for n in repos),
        "months": months,
        "langs": langs,
        "per_repo": per_repo,
        "dates": dates,
    }


# --------------------------------------------------------------- a cena

def month_seq(months: Counter) -> list:
    """Série contínua mês a mês, do primeiro ao último commit."""
    first, last = min(months), max(months)
    y0, m0 = int(first[:4]), int(first[5:7])
    y1, m1 = int(last[:4]), int(last[5:7])
    span = (y1 - y0) * 12 + (m1 - m0) + 1
    out = []
    for i in range(span):
        dy, dm = divmod(m0 - 1 + i, 12)
        key = f"{y0 + dy}-{dm + 1:02d}"
        out.append((key, months.get(key, 0)))
    return out


def scene(d: dict) -> str:
    """A tela única: histórico mensal como mapa de calor em blocos.

    Cada coluna é um mês, contíguas, com linha de base desenhada e escala
    declarada. Mês sem commit fica como célula apagada, visível.
    """
    W, H = 880, 400
    px = 4
    seq = month_seq(d["months"])
    peak = max((v for _, v in seq), default=1) or 1
    n = len(seq)

    fx, fy = 56, 132
    fw = W - 112
    rows = 6
    pitch = fw / max(n, 1)
    gw = max(3.0, pitch - 1.6)          # coluna quase encostada na vizinha
    row_h = 13
    base_y = fy + rows * row_h          # linha de base

    blocks = []
    for i, (key, v) in enumerate(seq):
        cx = fx + i * pitch
        if v == 0:
            blocks.append(
                f'<rect x="{cx:.1f}" y="{base_y - row_h + 2}" width="{gw:.1f}" '
                f'height="{row_h - 4}" fill="{DIM}" opacity="0.13"/>'
            )
            continue
        filled = max(1, round(rows * v / peak))
        color = AMBER if v == peak else PHOS
        op = 1.0 if v == peak else 0.42 + 0.58 * (v / peak)
        for r in range(filled):
            y = base_y - (r + 1) * row_h + 2
            blocks.append(
                f'<rect x="{cx:.1f}" y="{y}" width="{gw:.1f}" height="{row_h - 4}" '
                f'fill="{color}" opacity="{op:.2f}"/>'
            )

    # eixo de anos: marca alinhada ao primeiro mês de cada ano
    # uma marca por ano, no mês exato em que o ano vira
    axis = []
    for i, (key, _) in enumerate(seq):
        if key[5:7] == "01" or i == 0:
            x = fx + i * pitch
            axis.append(
                f'<rect x="{x:.1f}" y="{base_y}" width="1" height="6" fill="{DIM}" opacity="0.7"/>'
                + G.text(key[:4], x + 4, base_y + 12, px=2, color=DIM)
            )
    # separador vertical em cada virada de ano: torna os anos legíveis
    seps = []
    for i, (key, _) in enumerate(seq):
        if key[5:7] == "01":
            x = fx + i * pitch
            seps.append(f'<rect x="{x:.1f}" y="{fy - 4}" width="1" height="{base_y - fy + 4}" fill="{DIM}" opacity="0.16"/>')
    axis = "".join(axis)

    peak_key = next(k for k, v in seq if v == peak)
    callout = (G.text(f"{peak}", fx, fy - 24, 2, AMBER)
               + G.text(f" COMMITS EM {peak_key[5:]}/{peak_key[:4]}", fx + G.text_w(f"{peak}", 2) + 10, fy - 24, 2, DIM))
    # escala vertical declarada: quantos commits vale o topo
    scale = (G.text(f"TOPO = {peak}", W - 56 - G.text_w(f"TOPO = {peak}", 1), fy - 24, 1, DIM)
             + f'<rect x="{W-56}" y="{fy}" width="14" height="1" fill="{DIM}" opacity="0.6"/>'
             + G.text("0", W - 56 + 4, base_y - 8, 1, DIM))

    foot = (
        G.text(f"{d['commits']} COMMITS DESDE {min(d['months'])[:4]}", 56, H - 52, 2, INK)
        + G.text(f"{d['repos']} REPOS · {d['releases']} RELEASES", 56, H - 32, 2, DIM)
    )
    jw = G.text_w("JOGAR", 2)
    jogar = (
        G.text("JOGAR", W - 56 - jw, H - 52, 2, AMBER)
        + f'<rect x="{W - 56 - jw}" y="{H - 30}" width="{jw}" height="2" fill="{AMBER}"/>'
    )

    name = G.text("ITALO JEFERSON", 56, 40, 3, INK)
    sub = G.text("CADA COLUNA E UM MES", 56, 88, 2, DIM)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Historico mensal: {d['commits']} commits em {d['repos']} repositorios desde {min(d['months'])[:4]}, pico de {peak} em {peak_key[5:]}/{peak_key[:4]}">
  <rect width="{W}" height="{H}" fill="{GROUND}"/>
  {name}
  {sub}
  {callout}
  {scale}
  {''.join(blocks)}
  <rect x="{fx}" y="{base_y}" width="{fw}" height="1" fill="{DIM}" opacity="0.5"/>
  {axis}
  {foot}
  {jogar}
</svg>
'''


def scene_compact(d: dict) -> str:
    """A mesma história num canvas de celular, com corpo de texto 2x.

    O GitHub reduz a imagem para ~326px de largura no telefone; um texto de
    2px viraria pó. Aqui o canvas já é estreito, então o tamanho de tela cheia
    chega legível. Nenhum dado é escondido: as 44 colunas continuam todas.
    """
    W, H = 420, 404
    seq = month_seq(d["months"])
    peak = max((v for _, v in seq), default=1) or 1
    n = len(seq)

    fx, fy = 24, 190
    fw = W - 48
    rows = 5
    pitch = fw / max(n, 1)
    gw = max(2.0, pitch - 1.0)
    row_h = 16
    base_y = fy + rows * row_h

    blocks = []
    for i, (key, v) in enumerate(seq):
        cx = fx + i * pitch
        if v == 0:
            blocks.append(f'<rect x="{cx:.1f}" y="{base_y - row_h + 2}" width="{gw:.1f}" height="{row_h - 5}" fill="{DIM}" opacity="0.14"/>')
            continue
        filled = max(1, round(rows * v / peak))
        color = AMBER if v == peak else PHOS
        op = 1.0 if v == peak else 0.45 + 0.55 * (v / peak)
        for r in range(filled):
            y = base_y - (r + 1) * row_h + 2
            blocks.append(f'<rect x="{cx:.1f}" y="{y}" width="{gw:.1f}" height="{row_h - 5}" fill="{color}" opacity="{op:.2f}"/>')

    axis = []
    for i, (key, _) in enumerate(seq):
        if key[5:7] == "01":
            x = fx + i * pitch
            axis.append(f'<rect x="{x:.1f}" y="{base_y}" width="1" height="7" fill="{DIM}" opacity="0.7"/>'
                        + G.text(key[:4], x + 3, base_y + 14, 2, DIM))
    axis = "".join(axis)

    peak_key = next(k for k, v in seq if v == peak)
    # a data fica sob o PICO, não solta no meio: o bloco lê como unidade
    top = (G.text("PICO", fx, 100, 2, G.MUTED)
           + G.text(str(peak), fx, 122, 3, AMBER)
           + G.text("COMMITS", fx, 154, 2, G.MUTED)
           + G.text(f"{peak_key[5:]}/{peak_key[:4]}", fx + G.text_w("COMMITS", 2) + 12, 154, 2, G.MUTED))
    total = (G.text("TOTAL", W - 24 - G.text_w("TOTAL", 2), 100, 2, G.MUTED)
             + G.text(str(d["commits"]), W - 24 - G.text_w(str(d["commits"]), 3), 122, 3, INK)
             + G.text(f"{d['repos']} REPOS", W - 24 - G.text_w(f"{d['repos']} REPOS", 2), 154, 2, G.MUTED))

    # fecha o rodapé na borda inferior: nada de terço vazio no fim
    fy2 = H - 44
    foot = (G.text(f"{d['repos']} REPOSITORIOS · {d['releases']} RELEASES", fx, fy2 - 28, 2, G.MUTED)
            + G.text("TOQUE PARA JOGAR", fx, fy2, 2, AMBER)
            + f'<rect x="{fx}" y="{fy2 + 20}" width="{G.text_w("TOQUE PARA JOGAR", 2)}" height="2" fill="{AMBER}" opacity="0.6"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Historico mensal: {d['commits']} commits em {d['repos']} repositorios, pico de {peak} em {peak_key[5:]}/{peak_key[:4]}">
  <rect width="{W}" height="{H}" fill="{GROUND}"/>
  {G.text("ITALO JEFERSON", fx, 26, 2, INK)}
  {G.text("UM MES POR COLUNA", fx, 56, 2, DIM)}
  {top}
  {total}
  {''.join(blocks)}
  <rect x="{fx}" y="{base_y}" width="{fw}" height="1" fill="{DIM}" opacity="0.5"/>
  {axis}
  {foot}
</svg>
'''


def stack(d: dict, compact: bool = False) -> str:
    """Stack como dado: todas as linguagens, soma explícita, valores em tab stop.

    compact=True: canvas estreito, mesmo conteúdo, para o GitHub mobile.
    """
    langs = [(k, v) for k, v in d["langs"].most_common() if k]
    total = sum(v for _, v in langs) or 1
    SHORT = {"Jupyter Notebook": "JUPYTER", "TypeScript": "TS"}
    W = 420 if compact else 880
    row_h = 30 if compact else 21
    head = 78 if compact else 84
    H = head + row_h * len(langs) + 14

    LX = 24 if compact else 56
    BX = 150 if compact else 250
    RX = W - (24 if compact else 62)
    barmax = RX - BX - (46 if compact else 18)
    peak = max(v for _, v in langs) or 1

    rows = []
    y = head
    for i, (name, v) in enumerate(langs):
        w = max(3, int(barmax * v / peak))
        color = [PHOS, "#9B8CF0", AMBER, INK, "#5AC8FF", "#F07A7A", "#8AE07A"][i % 7]
        rows.append(
            G.text(SHORT.get(name, name).upper(), LX, y, 2, INK)
            + f'<rect x="{BX}" y="{y + 1}" width="{w}" height="{12 if compact else 11}" fill="{color}" opacity="0.9"/>'
            + G.text(str(v), RX - G.text_w(str(v), 2), y, 2, color)
        )
        y += row_h

    base = y - row_h + (20 if compact else 16)
    title = G.text("ONDE EU ESCREVO", LX, 26 if compact else 44, 2, INK)
    sub = G.text(f"{total} REPOS COM LINGUAGEM", LX, 52 if compact else 64, 2 if compact else 1, G.MUTED)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Linguagens: {', '.join(f'{k} {v}' for k, v in langs)}; total {total} repositorios">
  <rect width="{W}" height="{H}" fill="{GROUND}"/>
  {title}
  {sub}
  {''.join(rows)}
  <rect x="{LX}" y="{base}" width="{RX - LX}" height="1" fill="{DIM}" opacity="0.3"/>
</svg>
'''


def links(d: dict) -> str:
    """Três destinos numa linha, distribuídos na largura toda."""
    W, H = 880, 74
    items = [("LINKEDIN", PHOS), ("PORTFOLIO", "#9B8CF0"), ("E-MAIL", AMBER)]
    LX, RX = 56, W - 56
    widths = [G.text_w(lbl, 2) for lbl, _ in items]
    xs = [LX, (LX + RX) / 2 - widths[1] / 2, RX - widths[2]]
    parts = []
    for i, (label, color) in enumerate(items):
        x, w = xs[i], widths[i]
        parts.append(G.text(label, x, 26, 2, color))
        parts.append(f'<rect x="{x}" y="44" width="{w}" height="2" fill="{color}" opacity="0.55"/>')
        if i:
            mx = (xs[i-1] + widths[i-1] + x) / 2
            parts.append(f'<rect x="{mx:.0f}" y="22" width="1" height="26" fill="{DIM}" opacity="0.22"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Links: LinkedIn, portfolio e e-mail">
  <rect width="{W}" height="{H}" fill="{GROUND}"/>
  {''.join(parts)}
</svg>
'''


def link_chip(label: str, color: str) -> str:
    """Um destino só, para ser um alvo de clique individual no README."""
    w = G.text_w(label, 2)
    W, H = w + 16, 44
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label.title()}">
  {G.text(label, 8, 8, 2, color)}
  <rect x="8" y="28" width="{w}" height="2" fill="{color}" opacity="0.6"/>
</svg>
'''


def build(d: dict) -> dict:
    return {
        "scene": scene(d),
        "scene-mobile": scene_compact(d),
        "stack": stack(d),
        "stack-mobile": stack(d, compact=True),
        "chip-linkedin": link_chip("LINKEDIN", PHOS),
        "chip-portfolio": link_chip("PORTFOLIO", "#9B8CF0"),
        "chip-email": link_chip("E-MAIL", AMBER),
    }


def main() -> None:
    d = analyse(fetch())
    os.makedirs(OUT, exist_ok=True)
    for name, svg in build(d).items():
        path = os.path.join(OUT, f"{name}.svg")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(svg)
        os.replace(tmp, path)
    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump({k: v for k, v in d.items() if k not in ("dates",)},
                  f, ensure_ascii=False, indent=2, default=str)
    print(f"ok · {d['commits']} commits · {d['repos']} repos · "
          f"{len(month_seq(d['months']))} meses · top {d['per_repo'][0]['name']}")


if __name__ == "__main__":
    main()
