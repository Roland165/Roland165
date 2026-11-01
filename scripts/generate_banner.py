"""Generate the animated banner (banner.svg) for the GitHub profile README.

Stats are fetched from the GitHub API when GITHUB_TOKEN is set (the workflow
does this daily). Without a token, the FALLBACK values below are used.
"""

import json
import math
import os
import urllib.request
from pathlib import Path

USER = "Roland165"
OUT = Path(__file__).resolve().parent.parent / "banner.svg"

# ---------- Edit your content here ----------
NAME = "Roland Fontanes"
ROLE = "DATA SCIENTIST · AI ENGINEER"
TAGLINE = "Final-year engineering student · EFREI Paris"
SEEKING = "Open to internships · April 2027"

# (label, level) -> level: core | strong | working
SKILLS = [
    ("Python", "core"),
    ("SQL", "core"),
    ("LLMs · RAG", "core"),
    ("Azure", "strong"),
    ("PyTorch", "strong"),
    ("scikit-learn", "strong"),
    ("Power BI", "working"),
]

SCORE = [("Roland", [6, 5], "40"), ("LLM hallucinations", [2, 3], "15")]

FALLBACK = {"repos": 7, "contributions": None, "stars": 0, "top_lang": "Python"}
# --------------------------------------------

AMBER = "#ffb000"
ORANGE = "#ff7a1a"
TEXT = "#f5efe6"
MUTED = "#8f877c"
LEVEL_COLORS = {"core": AMBER, "strong": ORANGE, "working": "#7d7468"}
SANS = "Inter,'Segoe UI',-apple-system,Helvetica,Arial,sans-serif"


def _get(url, token, data=None):
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_stats():
    stats = dict(FALLBACK)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return stats
    try:
        repos = _get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner", token)
        owned = [r for r in repos if not r.get("fork")]
        stats["repos"] = len(repos)
        stats["stars"] = sum(r.get("stargazers_count", 0) for r in owned)
        langs = {}
        for r in owned:
            if r.get("language"):
                langs[r["language"]] = langs.get(r["language"], 0) + 1
        if langs:
            stats["top_lang"] = max(langs, key=langs.get)
    except Exception as e:  # keep fallback values
        print("REST error:", e)
    try:
        q = {"query": "query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{totalContributions}}}}",
             "variables": {"l": USER}}
        d = _get("https://api.github.com/graphql", token, json.dumps(q).encode())
        stats["contributions"] = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception as e:
        print("GraphQL error:", e)
    return stats


def skill_pills(x0, y0, max_w):
    out, x, y = [], x0, y0
    for label, lvl in SKILLS:
        w = round(len(label) * 7.1 + 30)
        if x + w > x0 + max_w:
            x, y = x0, y + 32
        c = LEVEL_COLORS[lvl]
        out.append(
            f'<g transform="translate({x},{y})">'
            f'<rect width="{w}" height="24" rx="12" fill="#ffffff" fill-opacity=".04" stroke="#ffffff" stroke-opacity=".1"/>'
            f'<circle cx="13" cy="12" r="3.5" fill="{c}"/>'
            f'<text x="23" y="16.5" font-size="12" fill="{TEXT}">{label}</text></g>')
        x += w + 8
    return "".join(out)


def build_svg(s):
    contrib = "–" if s["contributions"] is None else f"{s['contributions']:,}"
    kpis = [(contrib, "contributions / yr"), (str(s["repos"]), "public repos"), (s["top_lang"], "top language")]
    kpi_svg = ""
    for i, (val, lab) in enumerate(kpis):
        x = 40 + i * 130
        if i:
            kpi_svg += f'<line x1="{x-18}" y1="226" x2="{x-18}" y2="266" stroke="#ffffff" stroke-opacity=".1"/>'
        kpi_svg += (f'<text x="{x}" y="250" font-size="24" font-weight="700" fill="{TEXT}">{val}</text>'
                    f'<text x="{x}" y="268" font-size="11" fill="{MUTED}">{lab}</text>')

    # ---- Court (top-down, doubles 23.77 x 10.97 m) ----
    cx0, cy0, cw, ch = 480, 52, 380, 176
    sx, sy = cw / 23.77, ch / 10.97
    alley = 1.37 * sy
    svc = 6.40 * sx
    net = cx0 + cw / 2
    court = (
        f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="3" fill="#ffffff" fill-opacity=".025"/>'
        f'<g fill="none" stroke="{TEXT}" stroke-opacity=".55" stroke-width="1.2">'
        f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}"/>'
        f'<line x1="{cx0}" y1="{cy0+alley:.1f}" x2="{cx0+cw}" y2="{cy0+alley:.1f}"/>'
        f'<line x1="{cx0}" y1="{cy0+ch-alley:.1f}" x2="{cx0+cw}" y2="{cy0+ch-alley:.1f}"/>'
        f'<line x1="{net-svc:.1f}" y1="{cy0+alley:.1f}" x2="{net-svc:.1f}" y2="{cy0+ch-alley:.1f}"/>'
        f'<line x1="{net+svc:.1f}" y1="{cy0+alley:.1f}" x2="{net+svc:.1f}" y2="{cy0+ch-alley:.1f}"/>'
        f'<line x1="{net-svc:.1f}" y1="{cy0+ch/2}" x2="{net+svc:.1f}" y2="{cy0+ch/2}"/>'
        f'</g>'
        f'<line x1="{net}" y1="{cy0-8}" x2="{net}" y2="{cy0+ch+8}" stroke="{AMBER}" stroke-width="2.5" stroke-linecap="round"/>'
    )

    # Rally: hit points alternate left / right, bounce ~72% along each shot
    hits = [(500, 92), (842, 196), (500, 188), (842, 86)]
    pts = hits + [hits[0]]
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(4)]
    total = sum(seg)
    cum = [0.0]
    for L in seg:
        cum.append(cum[-1] + L / total)
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    kp = ";".join(f"{c:.4f}" for c in cum)
    kt = kp  # constant ball speed

    # Ball height (lift above its shadow) per shot: hit -> apex -> bounce -> hit
    h_times, h_vals = [], []
    for i in range(4):
        a, b = cum[i], cum[i + 1]
        for frac, h in ((0, 5), (0.38, 20), (0.72, 0), (0.86, 6)):
            h_times.append(a + (b - a) * frac)
            h_vals.append(h)
    h_times.append(1)
    h_vals.append(5)
    ht = ";".join(f"{t:.4f}" for t in h_times)
    hv = ";".join(f"0 {-v}" for v in h_vals)
    sc = ";".join(f"{1 + v/40:.3f}" for v in h_vals)

    dur = "4.8s"
    # Players slide to meet the ball
    lt = f"0;{cum[1]:.4f};{cum[2]:.4f};{cum[3]:.4f};1"
    left_y = f"{hits[0][1]};{hits[0][1]};{hits[2][1]};{hits[2][1]};{hits[0][1]}"
    right_y = f"{hits[3][1]};{hits[1][1]};{hits[1][1]};{hits[3][1]};{hits[3][1]}"
    spline = ";".join(["0.45 0 0.55 1"] * 4)

    players = (
        f'<circle cx="488" r="6" fill="{AMBER}"><animate attributeName="cy" dur="{dur}" repeatCount="indefinite" '
        f'values="{left_y}" keyTimes="{lt}" calcMode="spline" keySplines="{spline}"/></circle>'
        f'<circle cx="854" r="6" fill="{ORANGE}"><animate attributeName="cy" dur="{dur}" repeatCount="indefinite" '
        f'values="{right_y}" keyTimes="{lt}" calcMode="spline" keySplines="{spline}"/></circle>')

    ball = (
        f'<path d="{path}" fill="none" stroke="{AMBER}" stroke-opacity=".18" stroke-dasharray="3 5"/>'
        f'<g><animateMotion dur="{dur}" repeatCount="indefinite" path="{path}" keyPoints="{kp}" keyTimes="{kt}" calcMode="linear"/>'
        f'<ellipse rx="5" ry="3" fill="#000" opacity=".45"/>'
        f'<g><animateTransform attributeName="transform" type="translate" dur="{dur}" repeatCount="indefinite" values="{hv}" keyTimes="{ht}"/>'
        f'<g><animateTransform attributeName="transform" type="scale" dur="{dur}" repeatCount="indefinite" values="{sc}" keyTimes="{ht}"/>'
        f'<circle r="5" fill="#dfff4f"/><circle r="5" fill="none" stroke="#fff" stroke-opacity=".5"/></g></g></g>')

    # Scoreboard under the court
    sb = f'<g transform="translate(480,244)"><rect width="380" height="48" rx="10" fill="#ffffff" fill-opacity=".04" stroke="#ffffff" stroke-opacity=".08"/>'
    for r, (who, sets, pts_) in enumerate(SCORE):
        y = 20 + r * 18
        col = TEXT if r == 0 else MUTED
        if r == 0:
            sb += f'<circle cx="16" cy="{y-4}" r="3" fill="#dfff4f"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
        sb += f'<text x="28" y="{y}" font-size="12" font-weight="{600 if r == 0 else 400}" fill="{col}">{who}</text>'
        for j, v in enumerate(sets):
            sb += f'<text x="{290 + j*24}" y="{y}" font-size="12" font-weight="600" fill="{AMBER if r == 0 else MUTED}" text-anchor="middle">{v}</text>'
        sb += f'<text x="358" y="{y}" font-size="12" font-weight="700" fill="{AMBER if r == 0 else MUTED}" text-anchor="middle">{pts_}</text>'
    sb += "</g>"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 310" width="900" height="310" font-family="{SANS}">
<defs>
  <radialGradient id="g1" cx="0.78" cy="0.15" r="0.6">
    <stop offset="0" stop-color="{AMBER}" stop-opacity=".16"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g2" cx="0.05" cy="1" r="0.5">
    <stop offset="0" stop-color="{ORANGE}" stop-opacity=".10"/><stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="frame"><rect width="900" height="310" rx="16"/></clipPath>
</defs>
<g clip-path="url(#frame)">
  <rect width="900" height="310" fill="#0d0c0b"/>
  <rect width="900" height="310" fill="url(#g1)"/>
  <rect width="900" height="310" fill="url(#g2)"/>

  <!-- Availability pill -->
  <g transform="translate(40,30)">
    <rect width="232" height="24" rx="12" fill="{AMBER}" fill-opacity=".1" stroke="{AMBER}" stroke-opacity=".35"/>
    <circle cx="14" cy="12" r="3.5" fill="{AMBER}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>
    <circle cx="14" cy="12" r="3.5" fill="none" stroke="{AMBER}"><animate attributeName="r" values="3.5;9" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>
    <text x="26" y="16.5" font-size="12" font-weight="500" fill="{AMBER}">{SEEKING}</text>
  </g>

  <text x="40" y="84" font-size="11" font-weight="600" fill="{AMBER}" letter-spacing="2.5">{ROLE}</text>
  <text x="38" y="122" font-size="38" font-weight="700" fill="{TEXT}" letter-spacing="-0.5">{NAME}</text>
  <text x="40" y="146" font-size="14" fill="{MUTED}">{TAGLINE}</text>

  {skill_pills(40, 162, 400)}
  {kpi_svg}

  {court}
  {players}
  {ball}
  {sb}
</g>
<rect x=".5" y=".5" width="899" height="309" rx="16" fill="none" stroke="#ffffff" stroke-opacity=".08"/>
</svg>
'''


if __name__ == "__main__":
    stats = fetch_stats()
    OUT.write_text(build_svg(stats), encoding="utf-8")
    print("Wrote", OUT, stats)
