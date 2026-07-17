# CSE 4106 — Spatial Filters, Re-examined

**Three-presenter speaker script for the 17-slide deck.**
Target total: **8 minutes** (≈ 2.5 min per person).

---

## Roles

| Part | Slides | Presenter |
|---|---|---|
| **Part 1** — Problem & scope | 1 – 6 | Md. Safius Sifat (2103085) |
| **Part 2** — Filter design & demo | 7 – 12 | Tausif Muntak Tasin (2103076) |
| **Part 3** — Results, critique, close | 13 – 17 | Akibul Islam (2103066) |

> **House rule.** Hand off the laptop between parts. Don't read the slide.
> Use this as a *guide*, not a teleprompter.

---

## Part 1 — Problem & scope  (Md. Safius Sifat)

*Slides 1 – 6 · ≈ 2.5 min · ~330 words*

### Slide 1 — Title *(20 sec)*

Good morning, sir. We're Sifat, Tasin, and Akibul. This is our CSE 4106
project — *Spatial Filters, Re-examined*. We designed two custom filters,
AVGF and NGKCS, and compared them against four standard ones. Supervised
by Khaled Zinnurine sir.

### Slides 2 – 3 — Problem & evidence *(40 sec)*

Fluorescence microscopy is a Poisson–Gaussian noise field. Standard
denoisers force a bad trade: smooth and erase the cell, or sharpen and
amplify the noise. We asked: can a filter lean into the noise instead
of fighting it? Here's the evidence — same BBBC005 plate, clean on the
left, our "heavy" noise regime on the right. Cell boundaries dissolve.

### Slides 4 – 6 — Trade-off, method, scope *(60 sec)*

The standard filter family splits into four camps — linear smoothing,
non-linear smoothing, linear sharpening, mask-based sharpening. We
picked one from each: Box, Median, Sobel, Unsharp. We then designed two
custom filters. The scope: three public datasets, three noise regimes,
six filters, six metrics. Every number in part three is averaged across
those nine settings.

*(Hand off.)*

---

## Part 2 — Filter design & demo  (Tausif Muntak Tasin)

*Slides 7 – 12 · ≈ 2.5 min · ~330 words*

### Slides 7 – 9 — The four standards *(50 sec)*

Quick walkthrough. Box — arithmetic mean over a 3×3 window. Cheap, fast,
strong PSNR, but blurs edges. Median — sort the window, take the middle.
Preserves edges, no halos, highest SSIM among the standards. Sobel —
gradient operator, add the response back onto the image. Unsharp mask —
original minus a Gaussian-blurred copy. Both sharpeners reveal structure
but also amplify noise.

### Slide 10 — AVGF *(35 sec)*

Our first custom design: AVGF, Adaptive Variance-Gaussian Filter. It's a
Gaussian-weighted average whose per-pixel variance is gated by the local
variance. In plain terms — when local variance is high, it's an edge, so
don't smooth. When it's low and uniform, smooth hard. The sweep on the
right shows PSNR versus β — there's a clean peak around β = 1.5.

### Slide 11 — NGKCS *(35 sec)*

Our second custom design: NGKCS, Noise-Gated Kirsch Compass Sharpening.
Eight directional edge kernels, each gated by a noise-floor estimator.
If the local variance is below the floor, the direction is suppressed —
treated as noise. Above the floor, the response is sharpened. The sweep
shows Pratt's Figure of Merit versus σ_n. NGKCS reaches 0.598 — within
a hair of Box on this edge-localisation metric.

### Slide 12 — Visual demo *(20 sec)*

And here's the qualitative side. One representative case per dataset,
all six filters. Same field, six different readings. The trade-offs are
visible in one glance — Box and Median blur; Sobel and Unsharp amplify
noise-edges; AVGF and NGKCS keep the cell boundaries clean.

*(Hand off.)*

---

## Part 3 — Results, critique, close  (Akibul Islam)

*Slides 13 – 17 · ≈ 2.5 min · ~330 words*

### Slide 13 — Quantitative results *(40 sec)*

How did the custom designs do? Average PSNR across the nine settings:
Box 29.1, Median 28.2, AVGF 25.4, Noisy 21.8, NGKCS 21.1, Sobel 20.6,
Unsharp 16.6. PSNR rewards smoothing, so the sharpener NGKCS lands
near the noisy baseline — that's expected, not a flaw.

### Slide 14 — Canny overlay *(20 sec)*

Where NGKCS earns its keep is the Canny overlay. Same heavy-noise frame,
edges drawn on top of each filter's output. Look at AVGF and NGKCS —
clean cell-boundary edges, no noise-edges. The visual story is where
the custom designs recover.

### Slide 15 — Where the custom lands *(35 sec)*

Side by side, the trade-off table. PSNR — Box wins by 3.7 dB. SSIM —
Median wins at 0.701, AVGF trails at 0.476, NGKCS at 0.227. Pratt's
Figure of Merit — the edge-localisation metric — and here NGKCS
reaches 0.598, within 0.001 of Box. The story is consistent: smoothing
metrics go to the smoothers; the edge metric goes to the sharpener.

### Slide 16 — Honest limits *(30 sec)*

The honest answer: no custom design beats Box on this study. Box wins
PSNR. Median wins SSIM. NGKCS ties Box on Pratt's FoM — the one place
the custom recovers. The custom designs sit between the standards and
the noisy baseline on the averaged numbers, never first. They earn
their place on visual inspection, not on the averages.

### Slide 17 — Close + Q&A *(15 sec)*

To wrap — we designed two custom filters, tested them across three
datasets and three regimes against four standards. The standards still
win on the averages. The custom designs recover on the edge metric and
on visual inspection. Full pipeline and CSV are on the project disk.
Thank you — open for questions.

*(Q&A: Safius handles methodology, Tausif handles math, Akibul handles
metrics and results.)*

---

## Pacing tips for an 8-min run

- **Don't read the slides.** The numbers are on them. Your job is the
  *story* between the numbers.
- If you finish a slide early, **don't pad** — pause for one beat and
  move on. The audience needs the silence.
- If a part is running long, the easiest slide to skip is **slide 14**
  (Canny) — point at the NGKCS column on slide 12 instead, which
  shows the same idea.
- The handoff is a natural pause: say the next presenter's name and the
  audience will reset attention.

---

## Likely Q&A topics and who answers

| Question | Answer |
|---|---|
| Why Poisson + Gaussian specifically? | Safius — physics of the camera sensor |
| Why Sobel over Canny for the standard? | Tausif — Sobel is the canonical textbook gradient; Canny is non-maximum suppression, not a filter |
| Why β = 1.5 for AVGF? | Tausif — read off the sweep curve |
| What does Pratt's Figure of Merit actually measure? | Akibul — edge-localisation error between detected and ground-truth edges |
| Why does the custom lose on PSNR? | Akibul — PSNR is a smoothing metric; sharpener can't win it by construction |
| How long did the sweep take? | Safius — hours on a laptop, fully scripted in `scripts/` |
