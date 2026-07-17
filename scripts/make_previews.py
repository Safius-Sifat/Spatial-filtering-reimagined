"""Generate 3 single-slide style previews for the CSE 4106 spatial-filters deck.

Each preview shows ONE real animated title slide for the actual project, styled
in 3 distinct visual directions so the user can react visually rather than
guess from abstract names.

Output: docs/.frontend-slides/slide-previews/style-{a,b,c}.html
"""

from pathlib import Path

PREVIEW_DIR = Path(__file__).resolve().parents[1] / "docs" / ".frontend-slides" / "slide-previews"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

# All previews share the same viewport-base CSS and the same project chrome.
# They differ in palette, typography, and decorative vocabulary.

VIEWPORT_BASE_CSS = (Path(__file__).resolve().parents[1] / "results" / "_unused").exists()  # noqa
# Just paste the contents inline; we already have it in the cloned skill.
VIEWPORT_BASE = """
/* ===========================================
   FIXED 16:9 STAGE: MANDATORY BASE STYLES
   =========================================== */

html, body {
    width: 100%; height: 100%; margin: 0; overflow: hidden;
    background: var(--stage-bg, #000);
}

.deck-viewport {
    position: fixed; inset: 0; overflow: hidden;
    background: var(--stage-bg, #000);
}

.deck-stage {
    position: absolute; left: 0; top: 0;
    width: 1920px; height: 1080px;
    overflow: hidden; transform-origin: 0 0;
    background: var(--slide-bg, #fff);
}

.slide {
    position: absolute; inset: 0;
    width: 1920px; height: 1080px;
    overflow: hidden; display: block;
    visibility: hidden; opacity: 0; pointer-events: none;
    background: var(--slide-bg, #fff);
}

.slide.active, .slide.visible {
    visibility: visible; opacity: 1; pointer-events: auto; z-index: 1;
}

img, video, canvas, svg { max-width: 100%; max-height: 100%; }

.deck-controls {
    position: fixed; left: 50%; bottom: 22px;
    transform: translateX(-50%); z-index: 1000;
}

@media print {
    html, body { width: 1920px; height: auto; overflow: visible; background: #fff; }
    .deck-viewport { position: static; overflow: visible; background: #fff; }
    .deck-stage { position: static; width: auto; height: auto; transform: none !important; background: none; }
    .slide {
        position: relative; display: block !important; visibility: visible !important;
        opacity: 1 !important; pointer-events: auto !important;
        width: 1920px; height: 1080px; break-after: page; page-break-after: always;
    }
    .slide:last-child { break-after: auto; page-break-after: auto; }
    .deck-controls { display: none !important; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.2s !important;
    }
}
"""


def html_doc(style_id: str, style_label: str, fonts_url: str,
             css_body: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Spatial Filters — Preview ({style_label})</title>
<link rel="stylesheet" href="{fonts_url}">
<style>
{VIEWPORT_BASE}

{css_body}
</style>
</head>
<body>
<div class="deck-viewport">
  <main class="deck-stage">
    <section class="slide active visible">
      {body_html}
    </section>
  </main>
</div>
</body>
</html>
"""


# --------------------------------------------------------------------
# STYLE A: SWISS MODERN
# Pure white + black + red accent, Bauhaus grid, Archivo + Nunito
# --------------------------------------------------------------------
STYLE_A_BODY = """
.slide { background: #ffffff; color: #111; font-family: 'Nunito', sans-serif;
         position: relative; padding: 96px; }
.grid-bg {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(to right, rgba(0,0,0,0.04) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0,0,0,0.04) 1px, transparent 1px);
    background-size: 96px 96px;
    pointer-events: none;
}
.label { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 22px;
         letter-spacing: 0.18em; text-transform: uppercase; color: #ff3300;
         opacity: 0; transform: translateY(20px);
         animation: fadeUp 0.8s 0.2s cubic-bezier(0.16,1,0.3,1) forwards; }
.title { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 132px;
         line-height: 1.02; margin-top: 28px; max-width: 1500px;
         opacity: 0; transform: translateY(40px);
         animation: fadeUp 0.9s 0.45s cubic-bezier(0.16,1,0.3,1) forwards; }
.rule { width: 360px; height: 8px; background: #ff3300; margin-top: 40px;
        opacity: 0; transform: scaleX(0.2); transform-origin: left;
        animation: ruleGrow 0.7s 0.85s cubic-bezier(0.16,1,0.3,1) forwards; }
.sub { font-family: 'Nunito', sans-serif; font-weight: 400; font-size: 32px;
       line-height: 1.4; margin-top: 56px; max-width: 1200px; color: #222;
       opacity: 0; transform: translateY(20px);
       animation: fadeUp 0.8s 1.05s cubic-bezier(0.16,1,0.3,1) forwards; }
.meta { position: absolute; left: 96px; bottom: 80px;
        font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 18px;
        letter-spacing: 0.14em; text-transform: uppercase; color: #111;
        opacity: 0; animation: fadeUp 0.6s 1.3s cubic-bezier(0.16,1,0.3,1) forwards; }
.page { position: absolute; right: 96px; bottom: 80px;
        font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 18px;
        color: #111; opacity: 0;
        animation: fadeUp 0.6s 1.3s cubic-bezier(0.16,1,0.3,1) forwards; }
.red-dot { position: absolute; right: 96px; top: 96px;
           width: 56px; height: 56px; background: #ff3300; border-radius: 50%;
           opacity: 0; transform: scale(0.4);
           animation: pop 0.6s 0.1s cubic-bezier(0.34,1.56,0.64,1) forwards; }

@keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
@keyframes ruleGrow { to { opacity: 1; transform: scaleX(1); } }
@keyframes pop { to { opacity: 1; transform: scale(1); } }
"""

STYLE_A_HTML = """
<div class="grid-bg"></div>
<div class="red-dot"></div>
<div class="label">CSE 4106 — Digital Image Processing Lab</div>
<h1 class="title">Investigation of Spatial Filters<br/>for Noise-Robust Microscopy</h1>
<div class="rule"></div>
<p class="sub">Custom AVGF and NGKCS filters, evaluated against four standard
filters on three public datasets at three noise regimes.</p>
<div class="meta">RUET &nbsp; \u2022 &nbsp; July 2026</div>
<div class="page">01 / 20</div>
"""


# --------------------------------------------------------------------
# STYLE B: CREATIVE VOLTAGE
# Electric blue + neon yellow, Syne + Space Mono
# --------------------------------------------------------------------
STYLE_B_BODY = """
.slide { background: #1a1a2e; color: #fff; font-family: 'Space Mono', monospace;
         position: relative; overflow: hidden; }
.halftone {
    position: absolute; right: -120px; top: -120px;
    width: 760px; height: 760px;
    background-image: radial-gradient(circle, #d4ff00 1.5px, transparent 2.5px);
    background-size: 18px 18px;
    -webkit-mask-image: radial-gradient(circle at center, black 0%, transparent 65%);
            mask-image: radial-gradient(circle at center, black 0%, transparent 65%);
    opacity: 0; transform: rotate(20deg) scale(1.05);
    animation: drift 0.9s 0.15s cubic-bezier(0.16,1,0.3,1) forwards;
}
.left-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 96px;
            background: #0066ff; opacity: 0;
            animation: barIn 0.6s 0.2s cubic-bezier(0.16,1,0.3,1) forwards; }
.neon-tag {
    position: absolute; left: 156px; top: 140px;
    display: inline-block; padding: 14px 28px; background: #d4ff00; color: #1a1a2e;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 22px;
    letter-spacing: 0.18em; text-transform: uppercase;
    opacity: 0; transform: translateX(-20px);
    animation: fadeUp 0.6s 0.5s cubic-bezier(0.16,1,0.3,1) forwards;
}
.title {
    position: absolute; left: 156px; top: 220px; right: 760px;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 88px;
    line-height: 1.05; color: #fff;
    opacity: 0; transform: translateY(30px);
    animation: fadeUp 0.9s 0.7s cubic-bezier(0.16,1,0.3,1) forwards;
}
.title em { color: #d4ff00; font-style: normal; }
.sub {
    position: absolute; left: 156px; top: 820px; right: 156px;
    font-family: 'Space Mono', monospace; font-size: 20px; line-height: 1.5;
    color: rgba(255,255,255,0.85);
    border-left: 4px solid #d4ff00; padding-left: 18px;
    opacity: 0; transform: translateY(20px);
    animation: fadeUp 0.7s 1.1s cubic-bezier(0.16,1,0.3,1) forwards;
}
.meta {
    position: absolute; left: 156px; bottom: 96px;
    font-family: 'Space Mono', monospace; font-size: 18px; letter-spacing: 0.12em;
    color: #fff; text-transform: uppercase;
    opacity: 0; animation: fadeUp 0.5s 1.4s cubic-bezier(0.16,1,0.3,1) forwards;
}
.page {
    position: absolute; right: 96px; bottom: 96px;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 18px;
    color: #d4ff00; letter-spacing: 0.12em;
    opacity: 0; animation: fadeUp 0.5s 1.4s cubic-bezier(0.16,1,0.3,1) forwards;
}

@keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
@keyframes drift { to { opacity: 0.45; transform: rotate(20deg) scale(1.05); } }
@keyframes barIn { to { opacity: 1; } }
"""

STYLE_B_HTML = """
<div class="halftone"></div>
<div class="left-bar"></div>
<div class="neon-tag">CSE 4106 \u2022 Image Processing</div>
<h1 class="title">Spatial Filters<br/>for <em>Noise-Robust</em><br/>Microscopy.</h1>
<p class="sub">Two custom filters (AVGF, NGKCS) benchmarked against four standard filters across three public microscopy datasets and three Poisson\u2013Gaussian noise regimes.</p>
<div class="meta">RUET \u2022 July 2026</div>
<div class="page">01 / 20</div>
"""


# --------------------------------------------------------------------
# STYLE C: VINTAGE EDITORIAL
# Warm cream + Fraunces serif + Work Sans + abstract geometric ornaments
# --------------------------------------------------------------------
STYLE_C_BODY = """
.slide { background: #f5f3ee; color: #1a1a1a; font-family: 'Work Sans', sans-serif;
         position: relative; overflow: hidden; }
.paper-grain {
    position: absolute; inset: 0; opacity: 0.06; pointer-events: none;
    background-image:
        radial-gradient(circle at 25% 30%, #1a1a1a 0.5px, transparent 0.7px),
        radial-gradient(circle at 70% 70%, #1a1a1a 0.5px, transparent 0.7px);
    background-size: 6px 6px, 9px 9px;
}
.geom-circle {
    position: absolute; right: 140px; top: 200px;
    width: 280px; height: 280px; border: 3px solid #1a1a1a; border-radius: 50%;
    opacity: 0; transform: scale(0.6);
    animation: pop 0.9s 0.25s cubic-bezier(0.34,1.56,0.64,1) forwards;
}
.geom-line {
    position: absolute; left: 140px; bottom: 280px;
    width: 320px; height: 2px; background: #1a1a1a;
    opacity: 0; transform: scaleX(0.3); transform-origin: left;
    animation: ruleGrow 0.7s 0.55s cubic-bezier(0.16,1,0.3,1) forwards;
}
.geom-dot {
    position: absolute; left: 480px; bottom: 273px;
    width: 16px; height: 16px; background: #c41e3a; border-radius: 50%;
    opacity: 0;
    animation: pop 0.4s 0.95s cubic-bezier(0.34,1.56,0.64,1) forwards;
}
.eyebrow {
    position: absolute; left: 140px; top: 180px;
    font-family: 'Work Sans', sans-serif; font-size: 20px;
    letter-spacing: 0.30em; text-transform: uppercase; color: #c41e3a;
    opacity: 0; transform: translateY(15px);
    animation: fadeUp 0.6s 0.45s cubic-bezier(0.16,1,0.3,1) forwards;
}
.title {
    position: absolute; left: 140px; top: 240px; right: 140px;
    font-family: 'Fraunces', serif; font-weight: 900; font-style: italic;
    font-size: 132px; line-height: 0.98; color: #1a1a1a; letter-spacing: -0.02em;
    opacity: 0; transform: translateY(30px);
    animation: fadeUp 0.9s 0.6s cubic-bezier(0.16,1,0.3,1) forwards;
}
.title .quiet { font-style: normal; font-weight: 400; color: #555; }
.byline {
    position: absolute; left: 140px; bottom: 240px; right: 140px;
    font-family: 'Fraunces', serif; font-style: italic; font-size: 30px;
    color: #1a1a1a; line-height: 1.4;
    opacity: 0; transform: translateY(20px);
    animation: fadeUp 0.7s 1.0s cubic-bezier(0.16,1,0.3,1) forwards;
}
.byline .red { color: #c41e3a; font-style: normal; font-weight: 700; }
.meta {
    position: absolute; left: 140px; bottom: 120px;
    font-family: 'Work Sans', sans-serif; font-size: 16px;
    letter-spacing: 0.20em; text-transform: uppercase; color: #555;
    opacity: 0; animation: fadeUp 0.5s 1.3s cubic-bezier(0.16,1,0.3,1) forwards;
}
.page {
    position: absolute; right: 140px; bottom: 120px;
    font-family: 'Fraunces', serif; font-style: italic; font-size: 22px;
    color: #1a1a1a;
    opacity: 0; animation: fadeUp 0.5s 1.3s cubic-bezier(0.16,1,0.3,1) forwards;
}

@keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
@keyframes pop { to { opacity: 1; transform: scale(1); } }
@keyframes ruleGrow { to { opacity: 1; transform: scaleX(1); } }
"""

STYLE_C_HTML = """
<div class="paper-grain"></div>
<div class="geom-circle"></div>
<div class="geom-line"></div>
<div class="geom-dot"></div>
<div class="eyebrow">CSE 4106 \u2014 Lab Project Presentation</div>
<h1 class="title">Spatial Filters,<br/><span class="quiet">re&#8209;examined.</span></h1>
<p class="byline">Two <span class="red">custom designs</span> (AVGF, NGKCS)
evaluated against four standard filters on three public microscopy datasets.</p>
<div class="meta">Rajshahi University of Engineering &amp; Technology \u2022 July 2026</div>
<div class="page">i \u2014 <em>xx</em></div>
"""


PREVIEWS = [
    ("a", "Swiss Modern",
     "https://fonts.googleapis.com/css2?family=Archivo:wght@800&family=Nunito:wght@400;600&display=swap",
     STYLE_A_BODY, STYLE_A_HTML),
    ("b", "Creative Voltage",
     "https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Mono:wght@400;700&display=swap",
     STYLE_B_BODY, STYLE_B_HTML),
    ("c", "Vintage Editorial",
     "https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,700;0,900;1,400;1,700;1,900&family=Work+Sans:wght@400;500;600&display=swap",
     STYLE_C_BODY, STYLE_C_HTML),
]


def main() -> None:
    for sid, label, fonts, css, body in PREVIEWS:
        out = PREVIEW_DIR / f"style-{sid}.html"
        out.write_text(html_doc(sid, label, fonts, css, body), encoding="utf-8")
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()
