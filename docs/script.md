# CSE 4106 — Spatial Filters, Re-examined

**Three-person speaker script for the 17-slide deck.**
Target total: **12–15 minutes** (≈ 4 min per person).

---

## Roles

| Part | Slides | Presenter |
|---|---|---|
| **Part 1** — Problem & scope | 1 – 6 | Md. Safius Sifat (2103085) |
| **Part 2** — Filter design & demonstration | 7 – 12 | Tausif Muntak Tasin (2103076) |
| **Part 3** — Results, critique, close | 13 – 17 | Akibul Islam (2103066) |

> **House rule.** Hand off the laptop between parts. Don't read the slide.
> Look at the audience, point at the slide when you reference something,
> and use the script below as a *guide*, not a teleprompter.

---

## Part 1 — Problem & scope  (Md. Safius Sifat)

*Slides 1 – 6 · ≈ 4 min*

### Slide 1 — Title *(30 sec)*

Good morning/afternoon, sir. We're Md. Safius Sifat, Tausif Muntak Tasin, and
Akibul Islam, and this is our CSE 4106 lab project — *Spatial Filters,
Re-examined*. Over the next 12 or so minutes we'll walk you through two
custom filters we designed — we call them AVGF and NGKCS — and compare them
honestly against four standard ones. The project was supervised by
Khaled Zinnurine sir.

*(let the title slide do its work for a beat; the film strip on the right
shows the same field three times: original, noisy, and after our filter.)*

### Slide 2 — Problem *(40 sec)*

We work in fluorescence microscopy. The issue is that a microscope image is
never clean — there's always a mix of Poisson shot noise and Gaussian read
noise on top of the signal. Standard denoisers force a bad trade: either
they smooth out the noise and blur the cell boundaries, or they sharpen
edges and amplify the noise into noise-edges. So every filter in the box
trades one error for another. Our question was simple: can a filter be
designed that *leans into* the noise — uses the noise statistics as a
clue — rather than fighting them blindly?

### Slide 3 — Evidence *(30 sec)*

Here's the actual evidence. On the left is a clean field of human breast
cancer cells, BBBC005 plate B23. On the right is the same field under our
"heavy" noise regime. You can see the cell boundaries dissolve into
speckle. This is the regime where most of the interesting trade-offs show
up — and it's the regime we stress-test our filters on.

### Slide 4 — The trade-off *(45 sec)*

The standard-filter family breaks into four camps. Linear smoothing —
Box, Gaussian — averages neighbours with fixed weights, removes noise but
erases edges. Non-linear smoothing — Median, Bilateral — preserves edges
better, but drifts on textures. Linear sharpening — Sobel, Laplacian —
amplifies any noise pixel as if it were an edge. And mask-based sharpening
— Unsharp Mask — pulls halos around anything, and SSIM collapses under
heavy noise. So we picked one from each camp: Box, Median, Sobel sharpen,
and Unsharp mask. And then we asked, can we do better with a filter that
adapts to local variance?

### Slide 5 — Method *(30 sec)*

Four steps. We select three public microscopy datasets, three noise
regimes per dataset, six filter instances. We implement the four standards
from canonical formulations and design two custom filters. We run parameter
sweeps on the custom ones to find the sweet spot per regime. And we
compare quantitatively on six metrics, plus qualitatively on Canny
overlays. Everything you'll see is the output of one pipeline, averaged
across all nine dataset-by-regime settings.

### Slide 6 — Scope *(30 sec)*

So the scope: three datasets — BBBC005, Fluo-N2DH-GOWT1, BBBC034. Three
regimes — mild, realistic, heavy. Six filter instances — four standards,
two custom, plus the noisy baseline. Six metrics — PSNR, SSIM, MSE, EPI,
Pratt's Figure of Merit, and IoU on a binary segmentation pass. Every
number in the back half of the deck is an average across those nine
settings.

*(Hand off.)*

---

## Part 2 — Filter design & demonstration  (Tausif Muntak Tasin)

*Slides 7 – 12 · ≈ 4 min*

### Slide 7 — Box filter *(30 sec)*

Let's start with the workhorse. Box 3×3 — every output pixel is the
arithmetic mean of a 3×3 neighbourhood. It's linear, separable, fast, and
the reason it shows up everywhere. Cheap, parallelizable, gives you a
strong PSNR baseline. The cost: it blurs edges as if they were noise, and
you get those round halos on cells that wreck segmentation.

### Slide 8 — Median filter *(30 sec)*

Median — non-linear. Sort the 3×3 neighbourhood, take the middle value.
Handles salt-and-pepper style outliers cheaply, preserves edges (no
halos), and on our standard baselines it's the highest SSIM of the four.
It cannot recover lost signal — once the median erases a fine texture,
that texture is gone — and it's slower than Box on large kernels. But
it's the right default when segmentation fidelity matters.

### Slide 9 — Sobel & Unsharp *(30 sec)*

Now the sharpening paths. Sobel is a centred finite-difference gradient
operator — you can see the kernel here on the left. You apply it to the
noisy field and additively pull out the directional response back onto
the image. Unsharp mask is the older trick: take the original, subtract
a Gaussian-blurred copy, add the difference back. Both reveal structure,
both are required for downstream segmentation. The thing is, every noise
pixel becomes an edge — Sobel's noise-edge density wrecks SSIM, and
Unsharp's IoU collapses to zero on heavy noise.

### Slide 10 — AVGF *(45 sec)*

Now our first custom design. **AVGF** — Adaptive Variance-Gaussian
Filter. The math on the left: it's a Gaussian-weighted average, but the
per-pixel Gaussian *variance* is gated by the local variance of the
neighbourhood. In plain terms — when the local variance is high, you
have an edge, so you spread the Gaussian wide and you don't smooth.
When the local variance is low and uniform, you tighten up and smooth
aggressively. Homogeneous regions get cleaned; cell boundaries get
preserved. The parameter we tune is β, which controls how aggressively
the gate reacts to local variance. The sweep on the right shows PSNR
versus β averaged across our nine settings — there's a clean sweet spot
around β = 1.5, and the curve falls off if you go too high or too low.

### Slide 11 — NGKCS *(45 sec)*

Our second custom design. **NGKCS** — Noise-Gated Kirsch Compass
Sharpening. A Kirsch compass is eight directional edge kernels — north,
south, east, west, and the four diagonals. We compute all eight responses,
and gate each one through a noise-budget estimator. If the local
variance is below the noise floor, that direction's response is
suppressed — the filter assumes "this is just noise". When the local
variance exceeds the floor, the response is sharpened back. So instead
of amplifying noise as edges, we suppress it as noise. The sweep on the
right shows Pratt's Figure of Merit against the noise-floor threshold σ_n.
We get a peak FoM of 0.598 — which, importantly, is within a hair of
what Box achieves. The sharpening-pipeline metric is where directional
filters recover.

### Slide 12 — Six filters, three datasets *(40 sec)*

And here's the qualitative side. One representative case per dataset —
BBBC005 heavy, Fluo-N2DH-GOWT1 realistic, BBBC034 realistic — across all
six filters. Same field, same row, six different readings. You can see
the trade-offs in one glance: Box and Median blur cells; Sobel and
Unsharp amplify noise; AVGF sits in the middle, cleaner than the
standards but not as aggressive on denoising; NGKCS is the directional
sharpening of the noisy structure. Pick the column to read off which
filter does what.

*(Hand off.)*

---

## Part 3 — Results, critique, close  (Akibul Islam)

*Slides 13 – 17 · ≈ 4 min*

### Slide 13 — Quantitative results *(45 sec)*

So how did the custom designs actually do? Average PSNR across the nine
dataset-by-regime settings, on the left. Box 3×3 wins at 29.1 dB — that's
the smoothing-pipeline ceiling. Median comes second at 28.2. Our AVGF
sits at 25.4 — below both standards but well above the noisy baseline at
21.8. NGKCS, the sharpening filter, lands at 21.1, basically tied with
the noisy baseline on PSNR — because PSNR rewards smoothing, and
sharpening by definition can't beat smoothing on that metric.

### Slide 14 — Canny overlay *(30 sec)*

So if PSNR is a smoothing-pipeline metric, the Canny overlays are where
NGKCS earns its keep. Same BBBC005 heavy frame, Canny edges drawn on top
of each filter's output. Look at the original, look at the noisy — edges
everywhere, no signal. Look at Box and Median — clean edges, but round.
Look at Sobel and Unsharp — edges plus noise-edges, hard to tell apart.
Look at AVGF and NGKCS — clean cell-boundary edges, no noise-edges. The
qualitative sharpening story is where the custom designs deliver.

### Slide 15 — Where the custom lands *(45 sec)*

Side by side, the trade-off table. PSNR — Box wins by 3.7 dB over AVGF.
SSIM — Median wins at 0.701, AVGF trails at 0.476, NGKCS at 0.227, close
to the noisy baseline. MSE — same story as PSNR, Box wins. Pratt's
Figure of Merit — the edge-localisation metric — and here NGKCS reaches
0.598, within 0.001 of Box at 0.599. That's the one place the custom
designs recover. And IoU on a binary segmentation pass — Box at 0.858,
AVGF at 0.676, NGKCS at 0.267. The story is consistent: where smoothing
helps, Box and Median win. Where directional edges matter, the
sharpening-pipeline metric is where NGKCS pulls close.

### Slide 16 — Honest limits *(45 sec)*

So the honest answer is — *no custom design beats Box on this study.* On
PSNR, Box beats AVGF by 3.7 dB. On SSIM, Median wins at 0.701 and AVGF
trails at 0.476. The custom designs sit between the standards and the
noisy baseline, never first. The one place they pull close is Pratt's
FoM, where NGKCS gets within a hair of Box. So the strongest standard
wins across all three averaged metrics. The custom designs are *not* a
win on the averaged numbers. Where they do earn their place is the
qualitative visual story — clean edges without halos or noise-edges.

### Slide 17 — Closing + Q&A *(30 sec)*

So to wrap: we designed two custom filters, AVGF and NGKCS, and tested
them across three datasets and three noise regimes against four standard
baselines. The standard filters still win on the averaged metrics. The
custom designs recover on the edge-localisation metric and on visual
inspection. The full pipeline, all the figures, the CSV — everything's
on the project disk for you to dig into. Thank you — happy to take
questions.

*(Q&A begins. Hand-offs between the three of you as questions come in
on different topics — Safius handles methodology, Tausif handles the
math/filter questions, Akibul handles the metric and results questions.)*

---

## Pacing tips

- If you're running over time, the easiest slides to cut are **slide 4**
  (the four-camp trade-off matrix — you can summarise in one sentence
  during slide 3) and **slide 14** (the Canny overlay — point at slide
  12's NGKCS column instead).
- If a teammate finishes early, don't pad — ask the audience if they
  have a question on that section before handing off.
- The handoff is a natural pause: say "Tausif, over to you" / "Akibul,
  over to you" and the audience will reset attention.
