"""Regenerate the 'at a glance' card from live INSPIRE-HEP data.

Pulls the author's citation summary and publication list from the INSPIRE REST API
and writes assets/glance-{light,dark}.svg. Standard library only, so the GitHub
Action needs no dependencies. If INSPIRE is unreachable the existing cards are kept.

    python scripts/update_profile.py                 # live
    python scripts/update_profile.py --fixture f.json  # offline test
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

AUTHOR_BAI = "Mohammed.Boukidi.1"
EXCLUDE_ARXIV = {"2112.07502"}          # records not shown on the profile
COLLAB_AUTHORS = 100                    # larger author lists count as collaboration reports
FIRST_YEAR = 2022
API = "https://inspirehep.net/api"
UA = {"User-Agent": "MDBKD-profile-updater (github.com/MDBKD)", "Accept": "application/json"}

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

THEMES = {
    "light": dict(bg="#fbfbfa", border="#e6e5e1", ink="#0b0b0b", ink2="#52514e", ink3="#8a8985",
                  rule="#e6e5e1", bar="#2a78d6", tile="#ffffff", chip="#f1f0ec", accent="#2a78d6", live="#1baf7a"),
    "dark": dict(bg="#0d1117", border="#30363d", ink="#f0efec", ink2="#c3c2b7", ink3="#8b8a83",
                 rule="#30363d", bar="#3987e5", tile="#161b22", chip="#1c2128", accent="#3987e5", live="#199e70"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, 'DejaVu Sans', sans-serif"
SERIF = "Georgia, 'Times New Roman', 'DejaVu Serif', serif"
COLLABS = ["United Kingdom", "Sweden", "China", "Poland", "Morocco", "nCTEQ"]
COLLIDERS = ["LHC", "HL-LHC", "CLIC", "e⁺e⁻", "eγ", "γγ", "μp"]


# ----------------------------------------------------------------------------- data
def get(url: str, tries: int = 3) -> dict:
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception as exc:  # network hiccup or rate limit
            if k == tries - 1:
                raise
            print(f"retry {k + 1}: {exc}", file=sys.stderr)
            time.sleep(5 * (k + 1))
    raise RuntimeError("unreachable")


def fetch_live() -> dict:
    q = urllib.parse.quote(f"a {AUTHOR_BAI}")
    summary = get(f"{API}/literature/facets?q={q}&facet_name=citation-summary")
    fields = "titles,arxiv_eprints,citation_count,author_count,earliest_date,preprint_date,document_type,control_number"
    records = get(f"{API}/literature?q={q}&size=250&sort=mostrecent&fields={fields}")
    return {"summary": summary, "records": records}


def tex_to_text(s: str) -> str:
    rep = {r"\gamma": "γ", r"\mu": "μ", r"\nu": "ν", r"\tau": "τ", r"\to": "→", r"\rightarrow": "→",
           r"\pm": "±", r"\bar": "", r"\ell": "ℓ", r"\alpha": "α", r"\beta": "β", r"\eta": "η",
           r"\lambda": "λ", r"\chi": "χ", "^+": "⁺", "^-": "⁻", "^{+}": "⁺", "^{-}": "⁻", "^0": "⁰", "^{0}": "⁰",
           "^{\\pm}": "±", "^\\pm": "±", "_{W}": "W"}
    for a, b in rep.items():
        s = s.replace(a, b)
    s = re.sub(r"[${}\\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def digest(raw: dict) -> dict:
    agg = raw["summary"]["aggregations"]["citation_summary"]
    allb = agg["citations"]["buckets"]["all"]
    pub = agg["citations"]["buckets"]["published"]
    hits = [h["metadata"] for h in raw["records"]["hits"]["hits"]]

    def arxiv(m):
        e = m.get("arxiv_eprints") or []
        return e[0]["value"] if e else None

    own = [m for m in hits
           if (m.get("author_count") or 0) <= COLLAB_AUTHORS and arxiv(m) not in EXCLUDE_ARXIV]
    per_year: dict[int, int] = {}
    for m in own:
        date = m.get("earliest_date") or m.get("preprint_date") or ""
        if date[:4].isdigit() and int(date[:4]) >= FIRST_YEAR:
            per_year[int(date[:4])] = per_year.get(int(date[:4]), 0) + 1
    this_year = dt.date.today().year
    years = list(range(FIRST_YEAR, max([this_year] + list(per_year)) + 1))

    def title(m):
        return tex_to_text((m.get("titles") or [{"title": "?"}])[0]["title"])

    with_arxiv = [m for m in own if arxiv(m)]
    latest = max(with_arxiv, key=lambda m: m.get("earliest_date") or "") if with_arxiv else None
    top = max(own, key=lambda m: m.get("citation_count") or 0) if own else None
    return dict(
        citations=int(round(allb["citations_count"]["value"])),
        h_index=int(agg["h-index"]["value"]["all"]),
        published=int(pub["doc_count"]),
        avg_published=float(pub["average_citations"]["value"]),
        years=years, counts=[per_year.get(y, 0) for y in years],
        latest=(title(latest), arxiv(latest)) if latest else None,
        top=(title(top), top.get("citation_count") or 0, arxiv(top)) if top else None,
        updated=dt.date.today().isoformat(),
    )


# ----------------------------------------------------------------------------- render
def esc(s: str) -> str:
    return html.escape(s, quote=True)


def clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def caps(x, y, text, c, anchor="start"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{SANS}" font-size="12.5" '
            f'letter-spacing="2.2" fill="{c["ink3"]}">{text}</text>')


def tile(x, y, w, h, big, small, sub, c):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c["tile"]}" stroke="{c["border"]}"/>'
            f'<text x="{x + 20}" y="{y + 50}" font-family="{SERIF}" font-size="40" font-weight="600" fill="{c["ink"]}">{big}</text>'
            f'<text x="{x + 20}" y="{y + 75}" font-family="{SANS}" font-size="14.5" fill="{c["ink2"]}">{small}</text>'
            f'<text x="{x + 20}" y="{y + 95}" font-family="{SANS}" font-size="11.5" fill="{c["ink3"]}">{sub}</text>')


def chips(x, y, items, c, char_w=7.4, pad=12, gap=8):
    out, cx = [], x
    for it in items:
        w = len(it) * char_w + 2 * pad
        out.append(f'<rect x="{cx:.1f}" y="{y - 17}" width="{w:.1f}" height="26" rx="13" fill="{c["chip"]}" stroke="{c["border"]}"/>'
                   f'<text x="{cx + w / 2:.1f}" y="{y + 1}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{c["ink"]}">{it}</text>')
        cx += w + gap
    return "".join(out)


def render(d: dict, theme: str) -> str:
    c = THEMES[theme]
    W, H = 1280, 512
    aria = (f"At a glance, live from INSPIRE-HEP: {d['citations']} citations, h-index {d['h_index']}, "
            f"{d['published']} published papers; publications per year "
            + ", ".join(f"{y}: {n}" for y, n in zip(d["years"], d["counts"])))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(aria)}">',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="1.5"/>',
         caps(40, 50, "AT A GLANCE", c)]
    # live indicator
    o.append(f'<circle cx="190" cy="45.5" r="4" fill="{c["live"]}"><animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="201" y="50" font-family="{SANS}" font-size="12" fill="{c["ink3"]}">live from INSPIRE-HEP · {d["updated"]}</text>')

    tw, th, g, x0, y0 = 236, 106, 14, 40, 68
    o.append(tile(x0, y0, tw, th, f"{d['citations']:,}", "citations", "all INSPIRE records", c))
    o.append(tile(x0 + tw + g, y0, tw, th, str(d["h_index"]), "h-index", "INSPIRE-HEP", c))
    o.append(tile(x0, y0 + th + g, tw, th, str(d["published"]), "published papers", "JHEP · PRD · PLB · EPJC · NPB · JPG", c))
    o.append(tile(x0 + tw + g, y0 + th + g, tw, th, f"{d['avg_published']:.1f}", "citations per paper", "average over published papers", c))

    # bar chart
    cx, cy, cw, ch = 590, 72, 650, 196
    o.append(caps(cx, 50, "PUBLICATIONS PER YEAR", c))
    o.append(f'<text x="{cx + cw}" y="50" text-anchor="end" font-family="{SANS}" font-size="12" fill="{c["ink3"]}">'
             f'by year of first appearance · {d["years"][-1]} to date</text>')
    ymax = max(5, max(d["counts"]) + 2)
    step = 5 if ymax > 8 else 2
    base = cy + ch
    for v in range(0, ymax + 1, step):
        yy = base - ch * v / ymax
        o.append(f'<line x1="{cx + 34}" y1="{yy:.1f}" x2="{cx + cw}" y2="{yy:.1f}" stroke="{c["rule"]}" stroke-width="1"/>'
                 f'<text x="{cx + 24}" y="{yy + 4:.1f}" text-anchor="end" font-family="{SANS}" font-size="12" fill="{c["ink3"]}">{v}</text>')
    slot = (cw - 50) / len(d["years"])
    bw = min(64.0, slot * 0.44)
    for i, (yr, n) in enumerate(zip(d["years"], d["counts"])):
        bx = cx + 50 + i * slot + (slot - bw) / 2
        bh, r = ch * n / ymax, 4 if n else 0
        if n:
            o.append(f'<path d="M{bx:.1f},{base} L{bx:.1f},{base - bh + r:.1f} Q{bx:.1f},{base - bh:.1f} {bx + r:.1f},{base - bh:.1f} '
                     f'L{bx + bw - r:.1f},{base - bh:.1f} Q{bx + bw:.1f},{base - bh:.1f} {bx + bw:.1f},{base - bh + r:.1f} '
                     f'L{bx + bw:.1f},{base} Z" fill="{c["bar"]}"/>')
        o.append(f'<text x="{bx + bw / 2:.1f}" y="{base - bh - 9:.1f}" text-anchor="middle" font-family="{SANS}" font-size="14" font-weight="600" fill="{c["ink"]}">{n}</text>'
                 f'<text x="{bx + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{c["ink2"]}">{yr}</text>')
    o.append(f'<line x1="{cx + 34}" y1="{base}" x2="{cx + cw}" y2="{base}" stroke="{c["ink3"]}" stroke-width="1.2"/>')

    # latest and most cited
    yl = y0 + 2 * th + g + 22
    o.append(f'<line x1="40" y1="{yl}" x2="{W - 40}" y2="{yl}" stroke="{c["rule"]}"/>')
    if d.get("latest"):
        t, ax = d["latest"]
        o.append(caps(40, yl + 34, "LATEST", c))
        o.append(f'<text x="210" y="{yl + 34}" font-family="{SANS}" font-size="14.5" fill="{c["ink"]}">{esc(clip(t, 104))}'
                 f'<tspan dx="12" fill="{c["accent"]}">arXiv:{esc(ax)}</tspan></text>')
    if d.get("top"):
        t, n, ax = d["top"]
        o.append(caps(40, yl + 66, "MOST CITED", c))
        o.append(f'<text x="210" y="{yl + 66}" font-family="{SANS}" font-size="14.5" fill="{c["ink"]}">{esc(clip(t, 96))}'
                 f'<tspan dx="12" fill="{c["accent"]}">{n} citations</tspan></text>')
    yc = yl + 84
    o.append(f'<line x1="40" y1="{yc}" x2="{W - 40}" y2="{yc}" stroke="{c["rule"]}"/>')
    o.append(caps(40, yc + 37, "COLLABORATIONS", c))
    o.append(chips(210, yc + 36, COLLABS, c))
    o.append(caps(40, yc + 77, "COLLIDERS", c))
    o.append(chips(210, yc + 76, COLLIDERS, c, char_w=8.2))
    o.append("</svg>")
    return "".join(o)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, help="offline JSON with keys 'summary' and 'records'")
    args = ap.parse_args()
    try:
        raw = json.loads(args.fixture.read_text()) if args.fixture else fetch_live()
        data = digest(raw)
    except Exception as exc:
        print(f"INSPIRE unavailable, keeping current cards: {exc}", file=sys.stderr)
        return 0
    print(json.dumps({k: v for k, v in data.items()}, ensure_ascii=False))
    ASSETS.mkdir(exist_ok=True)
    changed = False
    for theme in THEMES:
        path = ASSETS / f"glance-{theme}.svg"
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        m = re.search(r"live from INSPIRE-HEP · (\d{4}-\d{2}-\d{2})", old)
        if m and render({**data, "updated": m.group(1)}, theme) == old:
            continue                      # only the date would change: keep the file
        path.write_text(render(data, theme), encoding="utf-8")
        changed = True
    print("cards updated" if changed else "no change in metrics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
