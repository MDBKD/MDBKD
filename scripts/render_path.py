"""'My path' timeline (light and dark): B.Sc. -> M.Sc. -> Ph.D. -> postdoc.

    python scripts/render_path.py      -> assets/path-{light,dark}.svg
"""
from pathlib import Path

W, H = 1280, 236
STEPS = [  # (years, title, place, detail)
    ("2021 – 2024", "Ph.D. in Physics", "Cadi Ayyad University, Morocco", "advisor: Prof. R. Benbrik"),
    ("2025 –", "Postdoctoral Researcher", "IFJ PAN, Kraków, Poland", "Department of Particle Theory · nCTEQ"),
]
THEMES = {
    "light": dict(bg="#fbfbfa", border="#e6e5e1", ink="#0b0b0b", ink2="#52514e", ink3="#8a8985",
                  line="#d9d7d0", node="#2a78d6", now="#eb6834", panel="#fbfbfa"),
    "dark": dict(bg="#0d1117", border="#30363d", ink="#f0efec", ink2="#c3c2b7", ink3="#8b8a83",
                 line="#30363d", node="#3987e5", now="#d95926", panel="#0d1117"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, 'DejaVu Sans', sans-serif"
SERIF = "Georgia, 'Times New Roman', 'DejaVu Serif', serif"


def esc(s):
    return s.replace("&", "&amp;")


def build(theme):
    c = THEMES[theme]
    x0, x1, y = 330, W - 330, 92
    xs = [x0 + i * (x1 - x0) / (len(STEPS) - 1) for i in range(len(STEPS))]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="My path: ' + esc("; ".join(f"{a} {b}, {p}" for a, b, p, _ in STEPS)) + '">',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="1.5"/>',
         f'<text x="40" y="44" font-family="{SANS}" font-size="12.5" letter-spacing="2.2" fill="{c["ink3"]}">MY PATH</text>',
         f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{c["line"]}" stroke-width="3" stroke-linecap="round"/>']
    # progress line drawing across, then a travelling spark
    L = x1 - x0
    o.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{c["node"]}" stroke-width="3" stroke-linecap="round" '
             f'stroke-dasharray="{L}" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="{L};0;0" keyTimes="0;0.6;1" dur="7s" repeatCount="indefinite"/></line>')
    for i, ((yrs, title, place, detail), x) in enumerate(zip(STEPS, xs)):
        last = i == len(STEPS) - 1
        col = c["now"] if last else c["node"]
        if last:
            o.append(f'<circle cx="{x:.1f}" cy="{y}" r="9" fill="none" stroke="{col}" stroke-width="2">'
                     f'<animate attributeName="r" values="9;20;9" dur="2.6s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.9;0;0.9" dur="2.6s" repeatCount="indefinite"/></circle>')
        o.append(f'<circle cx="{x:.1f}" cy="{y}" r="9" fill="{c["panel"]}" stroke="{col}" stroke-width="3"/>'
                 f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="{col}"/>')
        o.append(f'<text x="{x:.1f}" y="{y - 24}" text-anchor="middle" font-family="{SANS}" font-size="13" font-weight="600" fill="{col}">{yrs}</text>')
        o.append(f'<text x="{x:.1f}" y="{y + 40}" text-anchor="middle" font-family="{SERIF}" font-size="17" font-weight="600" fill="{c["ink"]}">{esc(title)}</text>')
        o.append(f'<text x="{x:.1f}" y="{y + 64}" text-anchor="middle" font-family="{SANS}" font-size="13.5" fill="{c["ink2"]}">{esc(place)}</text>')
        o.append(f'<text x="{x:.1f}" y="{y + 84}" text-anchor="middle" font-family="{SANS}" font-size="12" fill="{c["ink3"]}">{esc(detail)}</text>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "assets"
    out.mkdir(exist_ok=True)
    for t in THEMES:
        (out / f"path-{t}.svg").write_text(build(t), encoding="utf-8")
    print("wrote path cards")
