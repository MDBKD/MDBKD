"""Profile header: name block + animated collider event display (light and dark).

The event display is a schematic detector cross-section (tracker, ECAL, HCAL, muon system)
with an illustrative event: a diphoton pair (Higgs), two QCD jets, missing transverse
energy (neutrinos / dark matter) and a muon. Tracks draw outward, deposits light up,
the event fades and repeats. Without SMIL support the event is shown fully drawn.

    python scripts/render_header.py      -> assets/header-{light,dark}.svg
"""
import math
from pathlib import Path

W, H = 1280, 320
CX, CY = 1080, 152          # interaction point
R_TRK, R_ECAL0, R_ECAL1, R_HCAL0, R_HCAL1, R_MU0, R_MU1 = 46, 51, 65, 70, 90, 96, 110
DUR = 6.5                   # seconds per event

THEMES = {
    "light": dict(bg="#fbfbfa", border="#e6e5e1", ink="#0b0b0b", ink2="#52514e", ink3="#8a8985",
                  layer="#d9d7d0", ecal="#1baf7a", hcal="#eb6834", mu="#2a78d6", met="#6250d6",
                  trk="#52514e", accent="#2a78d6", glow="#eb6834"),
    "dark": dict(bg="#0d1117", border="#30363d", ink="#f0efec", ink2="#c3c2b7", ink3="#8b8a83",
                 layer="#2b323b", ecal="#199e70", hcal="#d95926", mu="#3987e5", met="#7d6bea",
                 trk="#c3c2b7", accent="#3987e5", glow="#d95926"),
}
SERIF = "Georgia, 'Times New Roman', 'DejaVu Serif', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, 'DejaVu Sans', sans-serif"
MATH = "'Times New Roman', Times, 'DejaVu Serif', serif"


def pol(r, deg):
    a = math.radians(deg)
    return CX + r * math.cos(a), CY - r * math.sin(a)


def arc_track(deg, curv, r_end):
    """Charged track: circular arc from the IP, bending by `curv` degrees at r_end."""
    pts = []
    for i in range(25):
        r = r_end * i / 24
        pts.append(pol(r, deg + curv * (r / r_end) ** 2))
    return pts


def path_d(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def draw(pts, color, width, t0, extra=""):
    L = length(pts)
    t1 = t0 + 0.12
    return (f'<path d="{path_d(pts)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-dasharray="{L:.0f}" stroke-dashoffset="0"{extra}>'
            f'<animate attributeName="stroke-dashoffset" values="{L:.0f};{L:.0f};0;0" '
            f'keyTimes="0;{t0:.2f};{t1:.2f};1" dur="{DUR}s" repeatCount="indefinite"/></path>')


def cell(r0, r1, deg, half, color, t0):
    """Calorimeter deposit: annular sector lighting up at time fraction t0."""
    a0, a1 = deg - half, deg + half
    p = [pol(r0, a0), pol(r1, a0), pol(r1, a1), pol(r0, a1)]
    d = (f"M{p[0][0]:.1f},{p[0][1]:.1f} L{p[1][0]:.1f},{p[1][1]:.1f} "
         f"A{r1},{r1} 0 0 0 {p[2][0]:.1f},{p[2][1]:.1f} L{p[3][0]:.1f},{p[3][1]:.1f} "
         f"A{r0},{r0} 0 0 1 {p[0][0]:.1f},{p[0][1]:.1f} Z")
    return (f'<path d="{d}" fill="{color}" opacity="0.85">'
            f'<animate attributeName="opacity" values="0;0;0.85;0.85" keyTimes="0;{t0:.2f};{t0 + 0.06:.2f};1" '
            f'dur="{DUR}s" repeatCount="indefinite"/></path>')


def label(deg, r, text, color, size=15, sub=None, sup=None):
    x, y = pol(r, deg)
    s = (f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" font-family="{MATH}" font-style="italic" '
         f'font-size="{size}" fill="{color}">{text}')
    if sub:
        s += f'<tspan font-size="{size * 0.62:.0f}" dy="4">{sub}</tspan>'
    if sup:
        s += f'<tspan font-size="{size * 0.62:.0f}" dy="{-12 if sub else -7}">{sup}</tspan>'
    return s + "</text>"


def build(theme):
    c = THEMES[theme]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Mohammed Boukidi, theoretical particle physicist. Animated collider event display: '
         f'a photon pair, two jets, missing transverse energy and a muon.">',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="1.5"/>']

    # ---- detector layers
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{(R_MU0 + R_MU1) / 2}" fill="none" stroke="{c["layer"]}" stroke-width="{R_MU1 - R_MU0}" opacity="0.45"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{(R_HCAL0 + R_HCAL1) / 2}" fill="none" stroke="{c["layer"]}" stroke-width="{R_HCAL1 - R_HCAL0}" opacity="0.8"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{(R_ECAL0 + R_ECAL1) / 2}" fill="none" stroke="{c["layer"]}" stroke-width="{R_ECAL1 - R_ECAL0}" opacity="0.55"/>')
    for r in (13, 23, 33, 43):
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{c["layer"]}" stroke-width="1"/>')
    for k in range(24):                                   # calorimeter segmentation
        a = k * 15
        x0, y0 = pol(R_ECAL0, a); x1, y1 = pol(R_HCAL1, a)
        o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{c["bg"]}" stroke-width="1.2"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="4" fill="{c["ink"]}"/>')

    # ---- event
    ev = []
    # H -> gamma gamma: neutral, no track; dashed line + ECAL towers
    for deg, t0 in ((62, 0.10), (-118, 0.10)):
        p = [pol(5, deg), pol(R_ECAL0 - 2, deg)]
        L = length(p)
        ev.append(f'<path d="{path_d(p)}" stroke="{c["ecal"]}" stroke-width="2" stroke-dasharray="5 4" fill="none" opacity="0.9"/>')
        ev.append(cell(R_ECAL0, R_ECAL1, deg, 6.5, c["ecal"], t0 + 0.12))
    # QCD jets: bundles of curved tracks + HCAL deposits
    for deg, t0 in ((168, 0.18), (8, 0.26)):
        for k, (off, curv) in enumerate(((-10, 9), (-4, -6), (3, 7), (9, -10), (0, 15))):
            ev.append(draw(arc_track(deg + off, curv, R_TRK), c["trk"], 1.4, t0 + 0.02 * k))
        ev.append(cell(R_HCAL0, R_HCAL1, deg, 9, c["hcal"], t0 + 0.16))
        ev.append(cell(R_ECAL0, R_ECAL1, deg, 6, c["hcal"], t0 + 0.14))
    # muon: track through every layer
    ev.append(draw(arc_track(-62, -8, R_MU1), c["mu"], 2.2, 0.34))
    # missing transverse energy
    mp = [pol(6, 112), pol(R_MU1 + 4, 112)]
    L = length(mp)
    ev.append(f'<path d="{path_d(mp)}" stroke="{c["met"]}" stroke-width="2.6" stroke-dasharray="7 5" fill="none"/>')
    ax, ay = pol(R_MU1 + 10, 112); bx, by = pol(R_MU1 - 4, 112 + 4); cx2, cy2 = pol(R_MU1 - 4, 112 - 4)
    ev.append(f'<polygon points="{ax:.1f},{ay:.1f} {bx:.1f},{by:.1f} {cx2:.1f},{cy2:.1f}" fill="{c["met"]}"/>')
    # collision flash
    ev.append(f'<circle cx="{CX}" cy="{CY}" r="6" fill="{c["glow"]}" opacity="0">'
              f'<animate attributeName="r" values="4;4;22;4" keyTimes="0;0.05;0.14;1" dur="{DUR}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0;0.9;0;0" keyTimes="0;0.05;0.16;1" dur="{DUR}s" repeatCount="indefinite"/></circle>')
    o.append('<g>' + "".join(ev) +
             f'<animate attributeName="opacity" values="1;1;0;1" keyTimes="0;0.86;0.97;1" dur="{DUR}s" repeatCount="indefinite"/></g>')

    # labels outside the detector
    o.append(label(62, R_MU1 + 16, "γ", c["ecal"], 17))
    o.append(label(-118, R_MU1 + 14, "γ", c["ecal"], 17))
    o.append(label(168, R_MU1 + 18, "jet", c["hcal"], 15))
    o.append(label(8, R_MU1 + 20, "jet", c["hcal"], 15))
    o.append(label(-62, R_MU1 + 18, "μ", c["mu"], 17))
    o.append(label(112, R_MU1 + 20, "E", c["met"], 15, sub="T", sup="miss"))

    # ---- name block
    o.append(f'<rect x="64" y="78" width="4" height="164" rx="2" fill="{c["accent"]}"/>')
    o.append(f'<text x="92" y="126" font-family="{SERIF}" font-size="56" font-weight="600" fill="{c["ink"]}" letter-spacing="0.3">Mohammed Boukidi</text>')
    o.append(f'<text x="94" y="166" font-family="{SANS}" font-size="22" fill="{c["ink2"]}">Theoretical particle physicist</text>')
    o.append(f'<text x="94" y="203" font-family="{SANS}" font-size="16" fill="{c["ink2"]}">'
             f'Higgs sectors · Neutrino masses &amp; dark matter · QCD &amp; nuclear PDFs · Vector-like quarks</text>')
    o.append(f'<text x="94" y="237" font-family="{SANS}" font-size="15" fill="{c["ink3"]}" letter-spacing="0.4">'
             f'IFJ PAN  Kraków   ·   nCTEQ collaboration   ·   BSMTools</text>')
    o.append(f'<text x="{W - 40}" y="{H - 12}" text-anchor="end" font-family="{SANS}" font-size="10.5" fill="{c["ink3"]}">'
             f'illustrative event · γγ, jets, missing energy, muon</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "assets"
    out.mkdir(exist_ok=True)
    for t in THEMES:
        (out / f"header-{t}.svg").write_text(build(t), encoding="utf-8")
        print("wrote", out / f"header-{t}.svg")
