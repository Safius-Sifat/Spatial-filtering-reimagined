"""Generate 3 single-slide title previews for the CSE 4106 deck.

For each shortlisted template, copy the template's template.html into a
preview folder, keep ONLY the cover slide + nav chrome + script (so the deck
runtime still works), and patch the cover content with the actual project
metadata (title, students, course, teacher, date).

Output: docs/.frontend-slides/slide-previews/style-<slug>.html
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = Path("/tmp/beautiful-html-templates/templates")
PREVIEW_DIR = ROOT / "docs" / ".frontend-slides" / "slide-previews"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

# Each entry: (out_slug, template_dir, deck_title, kicker, lede, meta_lines)
# Patch strategy: the scripts use string substitution on the *cover* section
# only, leaving the rest of the HTML untouched.

# 4th candidate: creative-mode — cream paper + multi-color accents + Archivo Black
_CM = {
    "slug": "04-creative-mode",
    "src_dir": TEMPLATES_ROOT / "creative-mode",
    # creative-mode uses a 2-row title with second row in --orange.
    # The original demo's title font-size is 160px which fits "CREATIVE" /
    # "MODE" (8 / 4 chars). Our content is 16 / 12 chars, so we tighten the
    # font-size to 130px and split row2 onto two lines.
    "title_font_size": "130px",
    "title_width": "900px",
    "title_row1": "Spatial Filters,",
    "title_row2_html": '<span style="display:block">re-</span><span class="row" style="color:var(--orange); display:block">examined.</span>',
    "tagline": "VOL.&nbsp;01 &nbsp;/&nbsp; CSE&nbsp;4106 &nbsp;/&nbsp; EDITION&nbsp;2026",
    "footnote": "An investigation of two custom spatial filters \u2014 AVGF and NGKCS \u2014 against four standard filters, across three public microscopy datasets and three Poisson\u2013Gaussian noise regimes.",
    "slide_meta_left": "RUET \u00b7 LAB PROJECT",
    "slide_total": 8,
}


def _patch_creative_mode(html: str, c: dict) -> str:
    """Patch the cover-slide content in the creative-mode template.

    creative-mode's cover structure:
      .tagline    — top-left mono uppercase with a leading rule
      .title      — left-center, two .row spans (row2 can be --orange)
      .footnote   — bottom-left, Space Grotesk body
      .poster     — right-side graphic block (left untouched — it's the signature)
      .slide-meta — bottom strip
    """
    cover_block = re.search(
        r'(<section class="s1"[^>]*>[\s\S]*?</section>)',
        html,
    )
    assert cover_block, "creative-mode cover section not found"

    new_cover = f'''<section class="s1" data-screen-label="01 Title">
    <div class="tagline">
      <span></span>{c["tagline"]}
    </div>

    <div class="title display" style="font-size:{c["title_font_size"]}; width:{c["title_width"]}">
      <span class="row">{c["title_row1"]}</span>
      {c["title_row2_html"]}
    </div>

    <div class="footnote">
      {c["footnote"]}
    </div>

    <div class="poster" aria-hidden="true">
      <div class="switch">
        <div class="lever"></div>
        <div class="label-on">
</div>
        <div class="label-off">
</div>
      </div>
    </div>

    <div class="slide-meta">
      <div>{c["slide_meta_left"]}</div>
      <div>01<span class="dot"></span>08</div>
    </div>
  </section>'''
    return html.replace(cover_block.group(1), new_cover, 1)


CANDIDATES = [
    # vellum — navy + chartreuse italic Cormorant, scholarly
    {
        "slug": "01-vellum",
        "src_dir": TEMPLATES_ROOT / "vellum",
        "title": "Spatial Filters,\nRe&#8209;examined.",
        "kicker": "CSE 4106 \u00b7 Digital Image Processing Lab",
        "lede": "An investigation of two custom spatial filters \u2014 AVGF and NGKCS \u2014 against four standard filters, across three public microscopy datasets and three Poisson\u2013Gaussian noise regimes.",
        "meta_lines": [
            "Md. Safius Sifat \u00b7 Tausif Muntak Tasin \u00b7 Akibul Islam",
            "Rajshahi University of Engineering &amp; Technology",
            "Submitted to Khaled Zinnurine, Lecturer",
            "July 2026",
        ],
        "slide_total": 9,
    },
    # monochrome — ivory ledger, all-ink, archival
    {
        "slug": "02-monochrome",
        "src_dir": TEMPLATES_ROOT / "monochrome",
        "title": "Investigation of Spatial<br />Filters",
        "kicker": "CSE 4106 \u00b7 Lab Project \u00b7 July 2026",
        "lede": "Two custom spatial filters (AVGF, NGKCS) benchmarked against four standard filters across three microscopy datasets and three noise regimes.",
        "meta_lines": [
            "Md. Safius Sifat \u00b7 Tausif Muntak Tasin \u00b7 Akibul Islam",
            "Submitted to Khaled Zinnurine, Lecturer",
            "RUET \u00b7 Department of Computer Science &amp; Engineering",
        ],
        "slide_total": 18,
    },
    # soft-editorial — Cormorant on warm paper, sage/blush/lemon, literary
    {
        "slug": "03-soft-editorial",
        "src_dir": TEMPLATES_ROOT / "soft-editorial",
        "title": "Spatial Filters, <em>noise&#8209;robust</em>.",
        "kicker": "A research debrief, vol. one",
        "lede": "An honest look at what happened when we put two custom spatial filters up against four standard ones \u2014 across three microscopy datasets and three Poisson\u2013Gaussian noise regimes.",
        "meta_lines": [
            "Md. Safius Sifat \u00b7 Tausif Muntak Tasin \u00b7 Akibul Islam",
            "July 2026 \u00b7 RUET \u00b7 CSE 4106",
            "Submitted to Khaled Zinnurine, Lecturer",
        ],
        "slide_total": 12,
    },
    _CM,
]


def _patch_vellum(html: str, c: dict) -> str:
    """Patch only the cover-slide content in the vellum template."""
    cover_block = re.search(
        r'(<section class="slide light slide--cover"[\s\S]*?</section>)',
        html,
    )
    assert cover_block, "vellum cover section not found"

    title_html = c["title"].replace("\n", "<br />")
    meta_html = "\n            ".join(
        f'<span class="pin-note">{m}</span>' for m in c["meta_lines"]
    )
    new_cover = f'''<section class="slide light slide--cover" data-slide="1" style="position: relative">
        <div class="cover-title">
          <span class="kicker">{c["kicker"]}</span>
          <h1 class="display">{title_html}</h1>
          <p class="lead" style="max-width: 70%; text-align: center; color: var(--c-fg-2)">
            {c["lede"]}
          </p>
        </div>
        <div class="pin-annotation">
          <span class="pin-note">01 / {c["slide_total"]:02d}</span>
          {meta_html}
        </div>
      </section>'''

    # Replace ONLY the first (cover) section. Leave the remaining slides intact.
    return html.replace(cover_block.group(1), new_cover, 1)


def _patch_monochrome(html: str, c: dict) -> str:
    """Patch the cover-slide content in the monochrome template."""
    cover_block = re.search(
        r'(<section class="slide slide--cover light">[\s\S]*?</section>)',
        html,
    )
    assert cover_block, "monochrome cover section not found"

    meta_html = "\n          ".join(
        f'<span class="label muted">{m}</span>' for m in c["meta_lines"]
    )
    new_cover = f'''<section class="slide slide--cover light">
        <!-- Sidebar: research context above, date below -->
        <div class="slide-sidebar" data-anim="fade-in" data-delay="0">
          <span class="sidebar-label">{c["kicker"]}</span>
          <span class="sidebar-label">July 2026</span>
        </div>

        <!-- Top-right deck label: title and date -->
        <div
          style="position: absolute; top: var(--pad-y); right: var(--pad-x); text-align: right;"
          data-anim="fade-in" data-delay="1"
        >
          <span class="label muted">Lab Project Defense / July 2026</span>
        </div>

        <div class="cover-body">
          <h1 class="display" data-anim="fade-up" data-delay="2">{c["title"]}</h1>
          <div class="rule" data-anim="reveal-right" data-delay="3" style="margin: 1.5vh 0"></div>
          <p class="lead muted" data-anim="fade-up" data-delay="4" style="max-width: 55%">{c["lede"]}</p>
        </div>

        <div class="cover-meta" data-anim="fade-in" data-delay="5">
          {meta_html}
        </div>
      </section>'''
    return html.replace(cover_block.group(1), new_cover, 1)


def _patch_soft_editorial(html: str, c: dict) -> str:
    """Patch the cover-slide content in the soft-editorial template."""
    cover_block = re.search(
        r'(<section class="slide s-cover"[^>]*>[\s\S]*?</section>)',
        html,
    )
    assert cover_block, "soft-editorial cover section not found"

    # The original is a bit bespoke: <div class="eyebrow">…</div>, swatches,
    # <div class="stack">kicker + h1 + lede</div>, footer. Reuse that shape.
    meta_html = "\n      ".join(f"<span>{m}</span>" for m in c["meta_lines"])
    new_cover = f'''<section class="slide s-cover" data-label="01 Cover">
    <div class="eyebrow">{c["kicker"]}</div>
    <div class="swatches" aria-hidden="true">
      <i style="background:var(--sage)"></i>
      <i style="background:var(--pink)"></i>
      <i style="background:var(--lemon)"></i>
    </div>
    <div class="stack">
      <div class="kicker">{c["meta_lines"][1]}</div>
      <h1>{c["title"]}</h1>
      <div class="lede">{c["lede"]}</div>
    </div>
    <div class="footer">
      {meta_html}
    </div>
  </section>'''
    return html.replace(cover_block.group(1), new_cover, 1)


def main() -> None:
    for c in CANDIDATES:
        src_html = (c["src_dir"] / "template.html").read_text(encoding="utf-8")
        slug = c["slug"]
        if slug.startswith("01-"):
            patched = _patch_vellum(src_html, c)
        elif slug.startswith("02-"):
            patched = _patch_monochrome(src_html, c)
        elif slug.startswith("03-"):
            patched = _patch_soft_editorial(src_html, c)
        elif slug.startswith("04-"):
            patched = _patch_creative_mode(src_html, c)
        else:
            raise RuntimeError(f"unknown slug {slug}")

        # Copy any sibling assets (deck-stage.js etc.) so the preview opens
        # self-contained.
        for sib in c["src_dir"].iterdir():
            if sib.is_file() and sib.name != "template.html":
                shutil.copy2(sib, PREVIEW_DIR / sib.name)

        out = PREVIEW_DIR / f"style-{slug}.html"
        out.write_text(patched, encoding="utf-8")
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()