"""Render the animated 'Research in motion' card (light and dark) as SVG.

Four panels, one per research line:
  Higgs      -- resonance scan over a falling background (schematic)
  Neutrinos  -- one-loop Scotogenic neutrino-mass diagram, pulse around the loop
  QCD        -- nuclear modification ratio R_A(x) with a breathing uncertainty band (schematic)
  VLQs       -- singlet-T exclusion: CMS arXiv:2604.17564 coupling limit + pair-production
                bound 1.485 TeV (VLQBounds)

Run:  python scripts/render_motion.py      (writes assets/motion-{light,dark}.svg)
Requires numpy and scipy (generation only; the SVGs are static files with SMIL animation).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

W, H = 1280, 372
PAD, GAP = 32, 16
PW = (W - 2 * PAD - 3 * GAP) / 4          # panel width
PY0, PH = 28, 316                          # panel top, height

THEMES = {
    "light": dict(bg="#fbfbfa", panel="#ffffff", border="#e6e5e1", ink="#0b0b0b", ink2="#52514e",
                  ink3="#8a8985", rule="#ecebe7", higgs="#eb6834", nu="#1baf7a", qcd="#2a78d6",
                  vlq="#6250d6", fill_q="#2a78d6", fill_v="#6250d6"),
    "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d", ink="#f0efec", ink2="#c3c2b7",
                 ink3="#8b8a83", rule="#262c33", higgs="#d95926", nu="#199e70", qcd="#3987e5",
                 vlq="#7d6bea", fill_q="#3987e5", fill_v="#7d6bea"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, 'DejaVu Sans', sans-serif"
MATH = "'Times New Roman', Times, 'DejaVu Serif', serif"


def pts(xy):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)


def poly_path(xy):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in xy)


def path_len(xy):
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(xy, xy[1:]))


def frame(x0, title, subtitle, c):
    return (f'<rect x="{x0:.1f}" y="{PY0}" width="{PW:.1f}" height="{PH}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>'
            f'<text x="{x0 + 18:.1f}" y="{PY0 + 30}" font-family="{SANS}" font-size="11.5" letter-spacing="1.9" fill="{c["ink3"]}">{title}</text>'
            f'<text x="{x0 + 18:.1f}" y="{PY0 + 51}" font-family="{SANS}" font-size="15" font-weight="600" fill="{c["ink"]}">{subtitle}</text>')


def caption(x0, text, c, y=None):
    y = PY0 + PH - 16 if y is None else y
    return f'<text x="{x0 + 18:.1f}" y="{y}" font-family="{SANS}" font-size="11" fill="{c["ink3"]}">{text}</text>'


def axes(bx0, by0, bx1, by1, c):
    return (f'<line x1="{bx0}" y1="{by1}" x2="{bx1}" y2="{by1}" stroke="{c["ink3"]}" stroke-width="1"/>'
            f'<line x1="{bx0}" y1="{by0}" x2="{bx0}" y2="{by1}" stroke="{c["ink3"]}" stroke-width="1"/>')


def mlabel(x, y, text, c, size=13, color=None, anchor="middle", italic=True):
    style = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{MATH}"{style} '
            f'font-size="{size}" fill="{color or c["ink2"]}">{text}</text>')


# --------------------------------------------------------------------------- Higgs
def panel_higgs(x0, c):
    o = [frame(x0, "EXTENDED HIGGS SECTORS", "Scanning for new scalars", c)]
    bx0, bx1, by0, by1 = x0 + 34, x0 + PW - 16, PY0 + 74, PY0 + PH - 70
    mlo, mhi = 70.0, 160.0
    X = lambda m: bx0 + (m - mlo) / (mhi - mlo) * (bx1 - bx0)
    g = lambda m, mu, s: np.exp(-0.5 * ((m - mu) / s) ** 2)
    model = lambda m: 1.0 * np.exp(-(m - mlo) / 38.0) + 0.16 * g(m, 125, 2.6) + 0.06 * g(m, 95, 3.2)
    ymax = 1.08
    Y = lambda v: by1 - v / ymax * (by1 - by0)
    ms = np.linspace(mlo, mhi, 240)
    o.append(axes(bx0, by0, bx1, by1, c))
    bkg = [(X(m), Y(np.exp(-(m - mlo) / 38.0))) for m in ms]
    o.append(f'<path d="{poly_path(bkg)}" fill="none" stroke="{c["ink3"]}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    curve = [(X(m), Y(model(m))) for m in ms]
    o.append(f'<path d="{poly_path(curve)}" fill="none" stroke="{c["higgs"]}" stroke-width="2.2"/>')
    rng = np.random.default_rng(7)
    for m in np.arange(72, 160, 4.0):
        v = model(m) * (1 + 0.06 * rng.standard_normal())
        o.append(f'<circle cx="{X(m):.1f}" cy="{Y(v):.1f}" r="2.2" fill="{c["ink2"]}"/>')
    # peaks: pulsing markers
    for m, dur, lab in ((95, "2.4s", "95"), (125, "2.4s", "125")):
        o.append(f'<circle cx="{X(m):.1f}" cy="{Y(model(m)):.1f}" r="5" fill="none" stroke="{c["higgs"]}" stroke-width="1.6">'
                 f'<animate attributeName="r" values="4;11;4" dur="{dur}" repeatCount="indefinite" begin="{0 if m == 125 else 1.2}s"/>'
                 f'<animate attributeName="opacity" values="0.9;0;0.9" dur="{dur}" repeatCount="indefinite" begin="{0 if m == 125 else 1.2}s"/></circle>')
        o.append(f'<line x1="{X(m):.1f}" y1="{by1}" x2="{X(m):.1f}" y2="{by1 + 5}" stroke="{c["ink3"]}"/>'
                 f'<text x="{X(m):.1f}" y="{by1 + 18}" text-anchor="middle" font-family="{SANS}" font-size="11" fill="{c["ink2"]}">{lab}</text>')
    # scan line
    o.append(f'<line x1="{bx0}" y1="{by0}" x2="{bx0}" y2="{by1}" stroke="{c["higgs"]}" stroke-width="1.2" opacity="0.55">'
             f'<animate attributeName="x1" values="{bx0};{bx1};{bx0}" dur="6s" repeatCount="indefinite"/>'
             f'<animate attributeName="x2" values="{bx0};{bx1};{bx0}" dur="6s" repeatCount="indefinite"/></line>')
    o.append(mlabel(bx1, by1 + 30, 'm<tspan font-size="9" dy="3">γγ</tspan><tspan dy="-3" font-style="normal"> [GeV]</tspan>', c, size=12, anchor="end"))
    o.append(mlabel(bx0 + 6, by0 + 4, "h, H, A", c, size=12, anchor="start", color=c["higgs"]))
    o.append(caption(x0, "2HDM: 95 GeV excess and h(125) · schematic", c))
    return "".join(o)


# --------------------------------------------------------------------------- neutrinos
def panel_nu(x0, c):
    o = [frame(x0, "NEUTRINO MASSES &amp; DARK MATTER", "Radiative masses at one loop", c)]
    yb = PY0 + 222
    L, V1, V2, R = (x0 + 22, yb), (x0 + 88, yb), (x0 + PW - 88, yb), (x0 + PW - 22, yb)
    r = (V2[0] - V1[0]) / 2
    mid = (V1[0] + r, yb - r)
    # fermion lines
    for a, b, col in ((L, V1, c["ink2"]), (V1, V2, c["nu"]), (V2, R, c["ink2"])):
        o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]}" x2="{b[0]:.1f}" y2="{b[1]}" stroke="{col}" stroke-width="{2.6 if col == c["nu"] else 2}"/>')
    # Majorana mass insertion
    cx = V1[0] + r
    o.append(f'<path d="M{cx - 6:.1f},{yb - 6} L{cx + 6:.1f},{yb + 6} M{cx - 6:.1f},{yb + 6} L{cx + 6:.1f},{yb - 6}" stroke="{c["nu"]}" stroke-width="2.2"/>')
    # eta loop (dashed semicircle) and vev insertions
    arc = f"M{V1[0]:.1f},{yb} A{r:.1f},{r:.1f} 0 0 1 {V2[0]:.1f},{yb}"
    o.append(f'<path d="{arc}" fill="none" stroke="{c["ink2"]}" stroke-width="2" stroke-dasharray="7 5"/>')
    for dx in (-34, 34):
        hx, hy = mid[0] + dx, mid[1] - 46
        o.append(f'<line x1="{mid[0]:.1f}" y1="{mid[1]:.1f}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{c["ink3"]}" stroke-width="1.6" stroke-dasharray="5 4"/>'
                 f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="6.5" fill="{c["panel"]}" stroke="{c["ink2"]}" stroke-width="1.4"/>'
                 f'<path d="M{hx - 4.6:.1f},{hy - 4.6:.1f} L{hx + 4.6:.1f},{hy + 4.6:.1f} M{hx - 4.6:.1f},{hy + 4.6:.1f} L{hx + 4.6:.1f},{hy - 4.6:.1f}" stroke="{c["ink2"]}" stroke-width="1.3"/>')
        o.append(mlabel(hx + (-14 if dx < 0 else 14), hy - 10, "⟨H⟩", c, size=12, anchor="end" if dx < 0 else "start", italic=False))
    for v in (V1, V2, mid):
        o.append(f'<circle cx="{v[0]:.1f}" cy="{v[1]:.1f}" r="3.6" fill="{c["ink"]}"/>')
    o.append(mlabel(mid[0], mid[1] + 18, 'λ<tspan font-size="9" dy="3">5</tspan>', c, size=12))
    o.append(mlabel(L[0] + 6, yb - 10, 'ν<tspan font-size="9" dy="3">α</tspan>', c))
    o.append(mlabel(R[0] - 6, yb - 10, 'ν<tspan font-size="9" dy="3">β</tspan>', c))
    o.append(mlabel(cx + 22, yb + 20, 'N<tspan font-size="9" dy="3">k</tspan>', c, color=c["nu"]))
    o.append(mlabel(V1[0] - 4, mid[1] + 26, 'η<tspan font-size="9" dy="-5">0</tspan>', c, anchor="end"))
    o.append(mlabel(V2[0] + 4, mid[1] + 26, 'η<tspan font-size="9" dy="-5">0</tspan>', c, anchor="start"))
    # pulse travelling through the diagram
    route = f"M{L[0]:.1f},{yb} L{V1[0]:.1f},{yb} A{r:.1f},{r:.1f} 0 0 1 {V2[0]:.1f},{yb} L{R[0]:.1f},{yb}"
    o.append(f'<circle r="5" fill="{c["nu"]}"><animateMotion dur="4.2s" repeatCount="indefinite" path="{route}"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.92;1" dur="4.2s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="{x0 + PW / 2:.1f}" y="{PY0 + PH - 40}" text-anchor="middle" font-family="{MATH}" font-size="13" fill="{c["ink"]}">'
             f'<tspan font-style="italic">m</tspan><tspan font-size="9" dy="3">ν</tspan><tspan dy="-3"> ∝ </tspan>'
             f'<tspan font-style="italic">λ</tspan><tspan font-size="9" dy="3">5</tspan><tspan dy="-3"> </tspan>'
             f'<tspan font-style="italic">v</tspan><tspan font-size="9" dy="-5">2</tspan><tspan dy="5"> Σ </tspan>'
             f'<tspan font-style="italic">Y</tspan><tspan font-size="9" dy="3">αk</tspan><tspan dy="-3" font-style="italic">Y</tspan>'
             f'<tspan font-size="9" dy="3">βk</tspan><tspan dy="-3"> / 32π</tspan><tspan font-size="9" dy="-5">2</tspan>'
             f'<tspan dy="5" font-style="italic">M</tspan><tspan font-size="9" dy="3">k</tspan></text>')
    o.append(caption(x0, "Scotogenic model · Z₂-odd loop · DM candidate", c))
    return "".join(o)


# --------------------------------------------------------------------------- QCD / nPDFs
def panel_qcd(x0, c):
    o = [frame(x0, "QCD &amp; NUCLEAR STRUCTURE", "Partons inside nuclei", c)]
    bx0, bx1, by0, by1 = x0 + 34, x0 + PW - 16, PY0 + 74, PY0 + PH - 70
    lx = np.array([-3.0, -2.5, -2.0, -1.5, -1.1, -0.85, -0.6, -0.4, -0.25, -0.15, -0.08, -0.03])
    rv = np.array([0.78, 0.83, 0.90, 0.99, 1.045, 1.035, 0.97, 0.90, 0.86, 0.88, 0.96, 1.12])
    f = PchipInterpolator(lx, rv)
    ylo, yhi = 0.62, 1.22
    X = lambda l: bx0 + (l + 3.0) / 3.0 * (bx1 - bx0)
    Y = lambda v: by1 - (v - ylo) / (yhi - ylo) * (by1 - by0)
    ls = np.linspace(-3.0, -0.03, 200)
    rr = f(ls)
    w = 0.025 + 0.055 * (-ls / 3.0) + 0.05 * np.exp((ls + 0.03) / 0.08)

    def band(scale):
        up = [(X(l), Y(v + scale * s)) for l, v, s in zip(ls, rr, w)]
        dn = [(X(l), Y(v - scale * s)) for l, v, s in zip(ls[::-1], rr[::-1], w[::-1])]
        return poly_path(up + dn) + " Z"

    o.append(axes(bx0, by0, bx1, by1, c))
    o.append(f'<line x1="{bx0}" y1="{Y(1):.1f}" x2="{bx1}" y2="{Y(1):.1f}" stroke="{c["ink3"]}" stroke-width="1" stroke-dasharray="4 3"/>')
    o.append(f'<path d="{band(1.0)}" fill="{c["fill_q"]}" opacity="0.18">'
             f'<animate attributeName="d" values="{band(1.0)};{band(1.7)};{band(1.0)}" dur="5s" repeatCount="indefinite"/></path>')
    curve = [(X(l), Y(v)) for l, v in zip(ls, rr)]
    L = path_len(curve)
    o.append(f'<path d="{poly_path(curve)}" fill="none" stroke="{c["qcd"]}" stroke-width="2.4" stroke-dasharray="{L:.0f}" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="{L:.0f};0;0" keyTimes="0;0.45;1" dur="6s" repeatCount="indefinite"/></path>')
    for l, v, lab, dy in ((-2.55, 0.83, "shadowing", 24), (-1.0, 1.045, "antishadowing", -14), (-0.32, 0.87, "EMC", 26), (-0.07, 1.08, "Fermi", -14)):
        o.append(f'<text x="{X(l):.1f}" y="{Y(v) + dy:.1f}" text-anchor="middle" font-family="{SANS}" font-size="10.5" fill="{c["ink2"]}">{lab}</text>')
    for l, lab in ((-3, "10⁻³"), (-2, "10⁻²"), (-1, "0.1"), (0, "1")):
        o.append(f'<line x1="{X(l):.1f}" y1="{by1}" x2="{X(l):.1f}" y2="{by1 + 5}" stroke="{c["ink3"]}"/>'
                 f'<text x="{X(l):.1f}" y="{by1 + 18}" text-anchor="middle" font-family="{SANS}" font-size="10.5" fill="{c["ink2"]}">{lab}</text>')
    o.append(mlabel(bx1, by1 + 30, "x", c, size=13, anchor="end"))
    o.append(mlabel(bx0 + 6, by0 + 4, 'R<tspan font-size="9" dy="3">A</tspan><tspan dy="-3">(x) = f</tspan><tspan font-size="9" dy="-5">p/A</tspan><tspan dy="5"> / f</tspan><tspan font-size="9" dy="-5">p</tspan>', c, size=12, anchor="start", color=c["qcd"]))
    o.append(caption(x0, "Nuclear PDFs · nCTEQ global analysis · schematic", c))
    return "".join(o)


# --------------------------------------------------------------------------- VLQs
MT = [700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400]
KT = [0.2451, 0.2173, 0.1466, 0.1412, 0.1578, 0.1662, 0.1264, 0.1221, 0.1452, 0.1766, 0.1901, 0.1719,
      0.1592, 0.1519, 0.1833, 0.2247, 0.2380, 0.2702]   # CMS arXiv:2604.17564 Fig. 4 (kappa_W^T), observed
M_PAIR = 1485.0                                           # VLQBounds pair-production limit, singlet T


def panel_vlq(x0, c):
    o = [frame(x0, "VECTOR-LIKE QUARKS", "Where can a heavy top hide?", c)]
    bx0, bx1, by0, by1 = x0 + 34, x0 + PW - 16, PY0 + 74, PY0 + PH - 70
    mlo, mhi, klo, khi = 800.0, 2400.0, 0.0, 0.45
    X = lambda m: bx0 + (m - mlo) / (mhi - mlo) * (bx1 - bx0)
    Y = lambda k: by1 - (k - klo) / (khi - klo) * (by1 - by0)
    o.append(axes(bx0, by0, bx1, by1, c))
    lim = [(X(m), Y(k)) for m, k in zip(MT, KT) if m >= mlo]
    region = poly_path([(X(mlo), Y(khi))] + lim + [(X(mhi), Y(khi))]) + " Z"
    o.append(f'<path d="{region}" fill="{c["fill_v"]}" opacity="0.14"/>')
    o.append(f'<rect x="{bx0}" y="{by0}" width="{X(M_PAIR) - bx0:.1f}" height="{by1 - by0}" fill="{c["fill_v"]}" opacity="0.10"/>')
    o.append(f'<line x1="{X(M_PAIR):.1f}" y1="{by0}" x2="{X(M_PAIR):.1f}" y2="{by1}" stroke="{c["vlq"]}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    Lp = path_len(lim)
    o.append(f'<path d="{poly_path(lim)}" fill="none" stroke="{c["vlq"]}" stroke-width="2.4" stroke-linejoin="round" '
             f'stroke-dasharray="{Lp:.0f}" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="{Lp:.0f};0;0" keyTimes="0;0.45;1" dur="6s" begin="1s" repeatCount="indefinite"/></path>')
    # a model point probed against the limits
    o.append(f'<circle cx="{X(2000):.1f}" cy="{Y(0.283):.1f}" r="4.5" fill="{c["vlq"]}">'
             f'<animate attributeName="r" values="3.5;6;3.5" dur="2.2s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="{(bx0 + X(M_PAIR)) / 2:.1f}" y="{by1 - 12}" text-anchor="middle" font-family="{MATH}" font-style="italic" font-size="12" fill="{c["vlq"]}">pp → T T̄</text>')
    o.append(f'<text x="{X(1950):.1f}" y="{by0 + 18}" text-anchor="middle" font-family="{MATH}" font-style="italic" font-size="12" fill="{c["vlq"]}">pp → T b q</text>')
    for m, lab in ((1000, "1"), (1500, "1.5"), (2000, "2")):
        o.append(f'<line x1="{X(m):.1f}" y1="{by1}" x2="{X(m):.1f}" y2="{by1 + 5}" stroke="{c["ink3"]}"/>'
                 f'<text x="{X(m):.1f}" y="{by1 + 18}" text-anchor="middle" font-family="{SANS}" font-size="10.5" fill="{c["ink2"]}">{lab}</text>')
    o.append(mlabel(bx1, by1 + 30, 'm<tspan font-size="9" dy="3">T</tspan><tspan dy="-3" font-style="normal"> [TeV]</tspan>', c, size=12, anchor="end"))
    o.append(mlabel(bx0 + 6, by0 + 4 + 0, 'κ<tspan font-size="9" dy="3">T</tspan>', c, size=13, anchor="start", color=c["vlq"]))
    o.append(caption(x0, "VLQBounds · CMS 2604.17564 + pair production", c))
    return "".join(o)


def build(theme: str) -> str:
    c = THEMES[theme]
    xs = [PAD + i * (PW + GAP) for i in range(4)]
    body = [panel_higgs(xs[0], c), panel_nu(xs[1], c), panel_qcd(xs[2], c), panel_vlq(xs[3], c)]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Research in motion: extended Higgs sectors, radiative neutrino masses, nuclear PDFs, vector-like quarks">'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="1.5"/>'
            + "".join(body) + "</svg>")


PANELS = {"higgs": panel_higgs, "nu": panel_nu, "qcd": panel_qcd, "vlq": panel_vlq}


def build_panel(name: str, theme: str) -> str:
    """One panel as a standalone image (used beside the text in the README)."""
    c = THEMES[theme]
    x0 = PAD
    body = PANELS[name](x0, c)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0 - 1:.1f} {PY0 - 1} {PW + 2:.1f} {PH + 2}" '
            f'width="{PW + 2:.0f}" height="{PH + 2}" role="img">' + body + "</svg>")


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "assets"
    out.mkdir(exist_ok=True)
    for t in THEMES:
        for name in PANELS:
            (out / f"panel-{name}-{t}.svg").write_text(build_panel(name, t), encoding="utf-8")
    print("wrote panel cards")
