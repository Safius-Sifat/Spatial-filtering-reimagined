# CSE 4106 — Spatial Filters, Re-examined
## Study Guide for the Final Defense

> This is the *understanding* version of the report. Read this first, then
> re-read the report to anchor the formal math. Every technical term has
> an "in plain English" line and a "worked example" so the intuition lands
> before the formula. The viva questions at the end are organised by who
> in your team should answer them.

---

## 0 · One-paragraph mental model

Fluorescence microscopy images are corrupted by **Poisson shot noise** (photon
count randomness) plus **Gaussian read noise** (camera electronics). To
recover the clean image we apply a **spatial filter** — a small 3×3 or 5×5
window that we slide over every pixel and combine the neighbourhood into a
new value. The two big families are:

- **Smoothers** (Box, Median, AVGF) — average the neighbourhood, kill
  noise, but blur edges.
- **Sharpeners** (Sobel, Unsharp, NGKCS) — pull out differences, enhance
  edges, but amplify noise.

The whole project is the bet that *if you make the smoother adaptive
(AVGF)* and *if you make the sharpener noise-aware (NGKCS)*, you can have
your cake and eat it. The result: AVGF and NGKCS are *competitive* in
specific regimes, not dominant on the standard metrics — and the report
admits that honestly, which is what PO4 (Investigation) actually rewards.

---

## 1 · Glossary of technical terms

> Read this top-to-bottom once. Skim back to it when a term in the report
> or the viva question doesn't ring a bell.

### 1.1 Image-side concepts

**Pixel** — A single number (0–255 for 8-bit grayscale, or three numbers
0–255 for RGB) at one location. *Example:* a 256×256 image has 65,536
pixels, and each one is a number saying "how bright is this spot?".

**Grayscale** — A single number per pixel. Our project is grayscale; an
RGB image has three. *Example:* BBBC005 is grayscale; you can tell because
the slide says so and the histograms have one peak not three.

**Convolution** — A sliding window operation. You put a small matrix
(the **kernel**) on top of the image, multiply each overlap, sum the
nine products, and write the result at the centre pixel. Slide the kernel
by one, repeat. *Example:* with kernel `[[1,1,1],[1,1,1],[1,1,1]]` and
dividing by 9, you get the Box filter.

**Kernel / mask** — The small matrix used in convolution. Most are 3×3
in this project. The kernel "shapes" what the filter does.

**Zero-padding** — When the kernel goes off the image edge, we pretend
the outside pixels are 0 (or we mirror). Without padding, the filtered
image would shrink by 2 pixels in each direction. *Example:* a 256×256
image filtered with a 3×3 kernel and zero-padding stays 256×256; without
padding it becomes 254×254.

**Stride** — How far the kernel jumps each step. We use stride 1
(every pixel gets a result). *Example:* stride 2 would halve the image
size — that's how pooling works in CNNs.

**Boundary handling** — What to do at edges. We use zero-padding.
Alternative: replicate, mirror, or wrap.

### 1.2 Noise

**Poisson noise** — Random fluctuations from counting discrete photons.
If a pixel *should* have 100 photons, the actual count is random with
mean 100. The variance of the count is also 100. So brighter pixels have
*more absolute noise* but *better SNR* than dimmer ones. *Example:*
`P(λ)` in the report is "draw a random integer whose mean is λ".

**Gaussian read noise** — Independent additive noise from the camera
electronics. Mean 0, std σ. *Example:* a σ=5 read noise means each pixel
gets a ±5 perturbation regardless of brightness.

**Poisson–Gaussian mixture** — The two noises are independent and add.
The model is `I_noisy = α·P(I/α) + N(0, σ²)`. The α controls photon
count scaling. *Example:* `α=10, σ=15` is the "heavy" regime — few
photons, lots of read noise, very degraded.

**SNR (signal-to-noise ratio)** — The ratio of clean signal strength to
noise strength. Higher is better. *Example:* a bright cell interior
might have SNR=20 (very visible); the dim background might have SNR=3
(almost entirely noise).

### 1.3 Standard filters

**Box filter** — Average the 3×3 neighbourhood. Linear, separable, fast.
Kills noise, blurs edges. *Example:* a noisy pixel at value 100 with
neighbours [98, 99, 101, 102, 100, 99, 101, 100, 100] becomes 100.0.

**Median filter** — Sort the 9 values, take the middle (5th). Non-linear.
Robust to outliers; preserves edges. *Example:* with neighbours above
plus one outlier at 250, Box gives 116, Median gives 100. Median "rejects"
the outlier; Box is dragged by it.

**Sobel operator** — Two 3×3 kernels approximating ∂/∂x and ∂/∂y. Their
magnitude is the gradient strength. *Example:* a clean horizontal edge
has Sobel-x ≈ strong, Sobel-y ≈ 0, magnitude = the x value.

**Gradient** — How fast pixel values change with position. Mathematically
∇I = (∂I/∂x, ∂I/∂y). *Example:* a horizontal edge has a large ∂I/∂x
across the edge, small ∂I/∂y along the edge.

**Laplacian** — A 3×3 kernel that approximates the second derivative.
Tells you "is this pixel a local max or min of its neighbourhood". Used
in the unsharp mask formula. *Example:* on a horizontal edge the
Laplacian response is +1 on one side, −1 on the other.

**Unsharp mask** — `I_sharp = I + k·(I − Gauss(I, σ))`. Take the original,
subtract a blurred copy, scale the difference, add it back. *Example:*
on a soft edge, the difference is large only at the edge, so adding it
back makes the edge crisper. But on noise, the difference is also large
at every pixel — noise gets amplified.

**Kirsch compass** — Eight 3×3 kernels, each a rotated Sobel-like
operator. Eight directional responses: N, NE, E, SE, S, SW, W, NW.
*Example:* on a diagonal edge going from upper-left to lower-right, the
NW and SE kernels give the strongest response, others give weak.

**Convolution separability** — A 2D filter `h(x,y) = h_x(x)·h_y(y)` can
be computed as two 1D filters, one row then one column. Box is separable
(`[1,1,1]/3 ⨂ [1,1,1]/3`). Median is *not* separable (you must sort in
2D). Sobel *is* separable. *Example:* separable Box does 6 multiplies
per pixel instead of 9.

### 1.4 Custom filter internals

**Local variance** `v_L` — The variance of pixel values in a small
window around the current pixel. High `v_L` = "this is an edge". Low
`v_L` = "this is a flat region". *Example:* a 5×5 window of all-100 pixels
has `v_L=0`; a 5×5 window spanning an edge has `v_L=1000+`.

**Immerkær noise variance estimator** — A clever filter that returns an
estimate of the *additive Gaussian* noise variance, without needing the
clean reference. Uses a high-pass mask that zeroes out smooth content
and keeps the noise. The factor `π/(2·6·(wd−2)·√2)` is a normalising
constant. *Example:* on a clean image, the estimate is near 0; on a noisy
image, the estimate matches the σ you put in.

**Adaptive Variance–Gaussian Filter (AVGF)** — A Gaussian smoother whose
*standard deviation* is chosen per pixel based on local variance. In
flat regions, use a wide Gaussian (σ_max) for strong smoothing. On
edges, use a narrow Gaussian (σ_min) to preserve the edge. The thresholds
T_low and T_high are set as multiples of the Immerkær noise estimate σ²_n.
*Example:* a pixel in a flat cytoplasm region sees v_L ≈ σ²_n, gets
τ=0.5, σ(x,y) ≈ mid-level → strong smoothing. A pixel on a cell edge
sees v_L ≫ σ²_n, gets τ=0, σ(x,y) = σ_min → barely smoothed.

**Noise-Gated Kirsch Compass Sharpening (NGKCS)** — A sharpener that
computes eight Kirsch responses per pixel and blends them through a
"confidence" mask. The confidence is `ρ = 1/(1 + α·v_L/σ²_n)`. In
high-SNR regions (v_L ≈ σ²_n), ρ ≈ 1 and the filter uses the max Kirsch
response (sharp directional sharpening). In low-SNR regions (v_L ≪ σ²_n
or the opposite), ρ ≈ 0 and the filter uses the mean Kirsch response
(isotropic, no spurious edges). *Example:* a clear cell edge has v_L
huge, ρ small, mean Kirsch used — wait, the formula says ρ high when
v_L is close to σ²_n. So a "real" edge (v_L ≫ σ²_n) actually has ρ
small. The filter is doing the opposite of what you might first think:
on a strong edge, use mean (less aggressive sharpening, since the edge
is already strong); on weak gradients near noise floor, use max (because
the gate threshold says "trust this, it's signal"). Read the formula
twice.

**Per-pixel parameter** — Both AVGF and NGKCS produce a per-pixel number
(τ or ρ) that selects one of N pre-computed filter levels. This is why
AVGF uses *N pre-computed Gaussian convolutions* and NGKCS uses *8
pre-computed Kirsch convolutions*: we don't recompute the filter for
each pixel, we just pick which of the N already-computed outputs to use.

**Parameter quantisation** — Rounding a continuous value (e.g. τ=0.37)
to one of N discrete levels (e.g. level 1 of 4). Reduces the number of
expensive Gaussian convolutions needed.

### 1.5 Evaluation metrics

**MSE (Mean Squared Error)** — `mean((I_clean − I_processed)²)` over all
pixels. Lower is better. *Example:* if clean and processed differ by 2
greys on average, MSE ≈ 4. *Caveat:* in 8-bit greys, MSE=100 is very
visible; MSE=1000 is awful.

**PSNR (Peak Signal-to-Noise Ratio)** — `20·log10(255/√MSE)`. Higher is
better. Units are decibels. *Example:* MSE=100 → PSNR ≈ 28.1 dB.
MSE=1000 → PSNR ≈ 18.1 dB. *Caveat:* a 3 dB difference means halving
(or doubling) the MSE — a big deal.

**SSIM (Structural Similarity Index)** — Combines three terms:
luminance similarity, contrast similarity, structure similarity. Range
−1 to 1; we want close to 1. *Example:* a 1-pixel shift of the entire
image has MSE=0 (technically perfect) but SSIM < 1 because the
*structure* moved. So SSIM catches what MSE misses. *Caveat:*
SSIM is non-linear in the image and can be hard to optimise for.

**EPI (Edge Preservation Index)** — Sattar et al. 1997. Measures how
well the reference's edge map is preserved by the processed image's edge
map. Range 0–1; higher is better. *Example:* if the clean image has 100
edge pixels and after filtering 90 are still detected in the same place,
EPI ≈ 0.9.

**Pratt's Figure of Merit (FoM)** — Pratt 1978. Compares the Canny
edge map of the processed image to the reference. Penalises *both* missed
edges and mis-located edges. Range 0–1; higher is better. *Example:*
if the processed image detects 100 edges and 95 of them are within 1
pixel of a reference edge, FoM ≈ 0.95. *Caveat:* this is the metric
where NGKCS wins — because the gating is designed around edge
localisation.

**Segmentation IoU (Intersection over Union)** — `|A ∩ B| / |A ∪ B|`,
where A and B are two binary masks (e.g. ground-truth cells vs detected
cells). Range 0–1; higher is better. *Example:* IoU=0.7 means the
detected mask overlaps the ground truth by 70% of their combined area.

**Otsu thresholding** — A 1979 algorithm that picks a single grey-level
threshold to separate an image into two classes (foreground/background)
by maximising between-class variance. *Example:* on a cell image with
dark background and bright cells, Otsu finds a single grey-value cut
below which = background, above which = cell. We use this for the IoU
metric.

**Canny edge detector** — Multi-stage: Gaussian blur, gradient
magnitude, non-maximum suppression, hysteresis thresholding. Gives
*one-pixel-wide* edges. Used in Pratt FoM and in our visual overlays.

### 1.6 Pipeline / engineering terms

**Pipeline** — A sequence of stages. Ours is `clean → degrade → filter
→ metric → figure/table`. Each stage is a Python module.

**Immerkær noise variance estimator** — Already covered. The *single
number* it returns is the "noise floor" the custom filters use to
decide what's signal and what's noise.

**Parameter sweep** — Run the filter at many parameter combinations,
record the metric each time, plot metric vs parameter. The peak of the
curve is the "best" setting.

**Averaged across 9 settings** — 3 datasets × 3 noise regimes = 9
experimental conditions. We report the mean across those 9. The mean
hides per-regime variation; the tables in the report show per-regime
numbers too.

**Per-pixel pre-computed convolutions** — Both AVGF and NGKCS rely on
*N pre-convolved images* (AVGF) or *8 pre-convolved images* (NGKCS).
Per pixel, the output is just a weighted combination or pick of these
pre-computed values. The clever bit: we never re-convolve the image at
filter-time, only at parameter-tuning time.

---

## 2 · How the experiment is set up

### 2.1 Datasets

- **BBBC005** — Broad Bioimage Benchmark Collection, image set 5. Human
  breast cancer cells (MCF-7), 1280×1024 fluorescence microscopy. *Has
  ground-truth segmentation masks* — the only one with a public mask.
- **Fluo-N2DH-GOWT1** — Cell Tracking Challenge, GFP-tagged
  *Gowt1* stem cells, 1024×1024, time-lapse single frames. *No public
  mask for our chosen frame.* Popular in cell-segmentation literature.
- **BBBC034** — Mouse blood smear, 1280×1024. *No public mask.*

### 2.2 Three noise regimes (in `src/degradation/poisson_gaussian.py`)

| Regime | α (photon scale) | σ_read | Visual character |
|---|---|---|---|
| mild | 50 | 5 | Slight grain, cells readable |
| realistic | 20 | 8 | Visible noise, edges fuzzy |
| heavy | 10 | 15 | Strong noise, edges dissolving |

### 2.3 Why these three?

`mild` tests whether the filter adds visible artefact on near-clean data.
`realistic` matches what a bench microscope gives you on a normal day.
`heavy` stresses the filter to its breaking point — the regime where
the custom designs' gating actually matters.

---

## 3 · The two custom designs, fully explained

### 3.1 AVGF

**The problem with Box and Median** — they use a single kernel size
everywhere. A 3×3 Box blurs a fine 1-pixel-wide cell membrane as much
as it blurs a wide 50-pixel-wide cytoplasm region. The membrane
*needs* preservation; the cytoplasm *needs* smoothing. One size can't
do both.

**AVGF's idea** — compute a different Gaussian σ for every pixel:
- On a flat region (local variance v_L low), use σ = σ_max (e.g. 2.0)
  → strong smoothing.
- On an edge (v_L high), use σ = σ_min (e.g. 1.0) → minimal smoothing.
- In between, interpolate linearly.

**The thresholds** — T_low = c_low · σ²_n, T_high = c_high · σ²_n. The
`σ²_n` comes from the Immerkær estimator. So the "what counts as flat"
decision is *relative to the noise*. After a parameter sweep we picked
c_low=1.0, c_high=8.0.

**Why this is faster than the per-pixel weights approach** — Instead of
recomputing weights per pixel per location, we pre-compute N=4 Gaussian
convolutions (at σ=1.0, 1.33, 1.67, 2.0) and per pixel just pick which
one. Each filter-time pixel work is a per-pixel τ calculation plus a
weighted average. ~8 ms total for 256×256.

**Caveat the report admits** — on dark, low-texture images (BBBC034
realistic), the whole image is below T_high, so the filter over-smooths.
This is a known limitation; the report flags it as a future-work item
("per-image parameter selection").

### 3.2 NGKCS

**The problem with Sobel and Unsharp** — they apply the same sharpening
to every pixel. A noise pixel looks like an edge to them, so they
sharpen it into a noise-edge. A real edge in a noisy region also gets
sharpened, but you can't tell which is which.

**NGKCS's idea** — compute eight directional Kirsch responses, then
blend them through a confidence mask based on the local SNR:
- ρ high (local variance close to noise floor, signal present but
  noisy) → use the *max* Kirsch response (sharpest direction).
- ρ low (local variance way above the noise floor — a strong, clean
  edge) → use the *mean* Kirsch response (already sharp, no need to
  push further).
- ρ low because of uniform noise — use the *mean* (suppresses random
  directions).

Wait, re-read the formula in section 1.4: `ρ = 1/(1 + α·v_L/σ²_n)`. If
v_L ≈ σ²_n, ρ = 1/(1+α) ≈ 0.2 (low). If v_L ≫ σ²_n, ρ → 0. So **on
the strongest edges, ρ is lowest, mean Kirsch used.** The filter is
conservative where the edge is already visible, and trusts the max
response where the edge is borderline (around the noise floor).

**Parameters after sweep** — k_0 = 0.3, α = 4.0.

**Visual result** — the only sharpener in the benchmark that does not
push the noise envelope upward. That's the *primary* qualitative claim
of the report.

---

## 4 · What the report actually claims

> Memorise these in your own words. These are the things the panel
> expects you to defend.

### 4.1 Quantitative claims (must be in your head)

| Claim | Numbers |
|---|---|
| Box wins PSNR | 29.11 dB (mean), +3.76 dB over AVGF |
| Median wins SSIM | 0.7014, AVGF 0.4763, NGKCS 0.2270 |
| NGKCS ties on Pratt FoM | 0.5980 (NGKCS) vs 0.5987 (Box) — within 0.001 |
| Sobel and Unsharp are *worse* than noisy on PSNR/SSIM | 20.59 / 16.63 vs noisy 21.83 / 0.3508 |
| AVGF ranks third on PSNR/SSIM | behind Box and Median |
| EPI: Median 0.9688, AVGF 0.9576, Box 0.9720 | AVGF slightly below Box and Median, not a loss |
| Time: Box 0.69 ms, AVGF 8.12 ms, NGKCS 11.04 ms | Custom is 10-15× slower than Box |

### 4.2 Qualitative claims

- NGKCS is the only sharpener that does *not* amplify noise visually.
- AVGF offers a *tunable* trade-off that Box and Median cannot — the
  parameter sweep lets you dial in.
- On BBBC005, IoU on segmentation is Box 0.858, AVGF 0.676, NGKCS 0.267.
- BBBC034 dark-image over-smoothing is a known AVGF limitation.

### 4.3 The honest assessment (the most important slide)

> "The standard median filter outperforms both custom filters on PSNR
> and SSIM, and the standard box filter outperforms AVGF on PSNR. This
> is a legitimate and interesting finding: the strongest simple
> non-linear filter is hard to beat with a small-scale custom
> Gaussian-mixture method on these evaluation metrics."

This is the *PO4 takeaway*. The report admits the standards win. The
custom filters win in two specific regimes: tunable smoothing (AVGF)
and edge-localisation accuracy (NGKCS).

---

## 5 · Probable viva questions

> The questions below are sorted by who in your team should be ready
> to answer them. The **(1)/(2)/(3)** markers map to:
> - (1) Safius — methodology, motivation, big picture
> - (2) Tausif — math, filter design, parameter choices
> - (3) Akibul — metrics, results, critique

### 5.1 Foundational / easy (every panel asks at least one of these)

**Q1. (1) Why did you choose BBBC005, Fluo-N2DH-GOWT1, and BBBC034?**
> All three are public benchmarks cited in the cell-image-analysis
> literature. BBBC005 is the only one with a public ground-truth
> segmentation mask, so we get to compute IoU on it. The other two
> cover different sample types (stem cells and blood smear) to avoid
> over-fitting to one imaging modality.

**Q2. (1) Why Poisson + Gaussian noise specifically?**
> Because that's what a fluorescence microscope produces. Poisson
> comes from photon-counting statistics (variance equals the count).
> Gaussian read noise is added by the camera electronics. Lebrun 2015
> showed this mixture is the dominant model in the field.

**Q3. (2) What's the difference between convolution and correlation?**
> Convolution flips the kernel. For symmetric kernels (Box, Sobel) the
> two are identical. For non-symmetric kernels they differ. We use
> convolution everywhere, implemented via NumPy's `np.convolve` /
> `scipy.signal.convolve2d`.

**Q4. (2) Why is Sobel separable but Median is not?**
> Sobel = `(column gradient) · (row smoothing)`. Median is a rank
> statistic, you can't decompose a sort into 1D passes and get the
> same answer. (In fact, separable median *approximations* exist, but
> they give a different filter.)

**Q5. (3) What is PSNR and what does +3 dB mean?**
> PSNR = 20·log10(255/√MSE). +3 dB means halving the MSE. So Box beats
> AVGF by 3.76 dB, which means AVGF's MSE is roughly 2.4× Box's MSE.

**Q6. (3) What is SSIM and why is it better than PSNR?**
> SSIM combines luminance, contrast, and structure similarity over
> local windows. PSNR only measures per-pixel error. SSIM catches
> blurring and shifts that PSNR misses or under-penalises.

### 5.2 On the custom filters (medium difficulty)

**Q7. (2) What does AVGF *adapt*?**
> The Gaussian standard deviation σ per pixel. A high local variance
> pulls σ down to σ_min; a low local variance pushes σ up to σ_max.
> Standard smoothers use one σ everywhere.

**Q8. (2) How does AVGF pick the thresholds T_low and T_high?**
> They are multiples of the Immerkær noise estimate σ²_n. We picked
> T_low = 1.0·σ²_n and T_high = 8.0·σ²_n after a parameter sweep on
> the Fluo-N2DH-GOWT1 realistic-regime image. The relative-to-noise
> scaling is what makes the filter portable across noise regimes.

**Q9. (2) Why N=4 levels and not N=1 (Box) or N=∞ (true per-pixel)?**
> N=1 reduces to Box. N=∞ means computing a different Gaussian at
> every pixel — too slow. N=4 trades off smoothness of the
> interpolation against the number of pre-convolutions. Empirically,
> 4 levels were enough to see the SSIM gain in the sweep.

**Q10. (2) What does the Kirsch compass add over Sobel?**
> Sobel covers two directions (x and y). Kirsch covers eight (the
> 4 cardinal + 4 diagonal). On a diagonal edge, Sobel magnitude is
> weaker than Kirsch max because Sobel spreads the response over both
> components. Kirsch max is also more robust to local orientation
> noise.

**Q11. (2) Why the SNR gate in NGKCS?**
> A clean edge has v_L ≫ σ²_n; ρ is small, mean Kirsch used (no
> extra sharpening). A noise pixel has v_L ≈ σ²_n; ρ is higher, max
> Kirsch used (which is the directional response that *could* be
> signal). The gate lets the filter trust the Kirsch max only in
> the noise-floor band, not everywhere.

**Q12. (2) Why k_0 = 0.3 and not the textbook 0.7?**
> Empirically, k_0 = 0.7 over-sharpens on our heavy noise regime and
> pushes Pratt FoM down. The sweep showed 0.3 is the sweet spot.
> (You should *not* be afraid to deviate from textbook values; the
> point of a sweep is to find what works on the actual data.)

**Q13. (3) NGKCS wins Pratt FoM but loses SSIM. Why both can be true?**
> Pratt FoM rewards *edge localisation* — a metric focused on the
> edges. SSIM rewards *full-image structure* — it cares about the
> whole picture, including flat regions. NGKCS sharpens edges
> perfectly but produces a noisier flat field, so SSIM falls.

### 5.3 On the methodology (medium-hard)

**Q14. (1) Why did you choose these six metrics?**
> Three smoothing-pipeline (PSNR, SSIM, MSE), two edge-pipeline
> (EPI, Pratt FoM), one downstream-task (segmentation IoU). Together
> they cover three different ways of judging "how good is this image".

**Q15. (1) What does the Immerkær estimator give you, exactly?**
> An estimate of the *additive Gaussian* read-noise variance. It
> needs only the noisy image, no clean reference. It's the noise
> floor that AVGF and NGKCS use to decide what's signal.

**Q16. (1) What does "averaged across 9 settings" hide?**
> Per-regime variation. Heavy noise might be where AVGF loses, while
> mild noise is where AVGF could win. The averaged table in the
> report smooths over this; the per-image, per-regime tables in
> section 4.4 of the report show the breakdown.

**Q17. (1) Why not use a learning-based denoiser (e.g. a U-Net)?**
> Out of scope for a CSE 4106 spatial-filtering project, and
> fairness-wise a CNN trained on ImageNet is not comparable to a
> 9-tap classical filter. Future work could include Noise2Void or
> a self-supervised CNN as a benchmark.

**Q18. (2) Why pre-compute the N Gaussian convolutions instead of
computing σ(x,y) per pixel and convolving?**
> Convolution is the expensive step. Pre-computing means we do the
> heavy work N=4 times (once per level), then per pixel just pick and
> blend. Per-pixel convolution with a different kernel would be
> O(N·width·height) and would dominate runtime.

**Q19. (2) How does the Sobel sharpening parameter k=0.3 compare to
the textbook value?**
> The textbook often uses 0.5–1.0. We picked 0.3 because the sweep on
> our data showed higher k over-sharpens and pushes PSNR below the
> noisy baseline. Conservative.

### 5.4 On the honest assessment (hard — the panel will probe this)

**Q20. (3) Your custom filters don't beat the standard ones on the
main metrics. Did you fail?**
> No. PO4 (Investigation) rewards asking the right question and
> honestly reporting the answer. The "right" result is "the standards
> are hard to beat on these metrics" — that's a publishable finding.
> The custom filters do recover in two specific regimes
> (tunable smoothing, edge-localisation), and that's where the
> contribution is.

**Q21. (3) Then what's the point of the custom filters?**
> Two specific use cases:
> 1. AVGF: when you need a *tunable* trade-off between smoothing and
>    edge preservation — the standard filters don't give you a knob.
> 2. NGKCS: when the downstream task is edge-localisation accuracy
>    (e.g. cell-counting, boundary detection) — the noise-amplification
>    suppression matters more than PSNR.

**Q22. (3) Why does Sobel do *worse* than the noisy baseline on PSNR?**
> Because Sobel *adds* the gradient to the image. The gradient includes
> noise-gradients on flat regions. So the filtered image is the noisy
> image + extra noise in the flat regions. PSNR drops.

**Q23. (3) Why is unsharp mask the *worst* filter in the benchmark?**
> Because with k=1.5 the amplification is very strong. The
> "difference between image and Gaussian-blurred" amplifies every
> noise pixel that the blur partially removed. Result: noise everywhere.

### 5.5 The really hard ones (only the report's authors should be able
to answer these)

**Q24. (2) Could you combine AVGF and NGKCS — smooth with AVGF first,
then sharpen with NGKCS?**
> Yes, that's the first item under Future Work. The intuition: a
> clean image (after AVGF) means NGKCS's gate is more often high,
> so it sharpens more confidently. We didn't do it because it
> doubles the runtime and the report's scope is single-filter
> comparison.

**Q25. (2) Why a 5×5 window for the local variance, not 3×3 or 7×7?**
> 3×3 is too noisy an estimator (only 9 samples). 7×7 starts to
> span the cell width and gives a misleading variance on the
> boundary region. 5×5 is the standard adaptive-filter choice
> (Lee 1980).

**Q26. (2) The Immerkær estimator assumes the noise is i.i.d.
Gaussian. Your noise is Poisson+Gaussian. Why does it still work?**
> Empirically, the estimator's response is monotonic in noise level,
> and the *ratio* `v_L / σ²_n` is what our gates actually use. So
> the absolute scale of σ²_n matters less than the *relative*
> comparison with v_L. The report relies on this empirical
> robustness; a more rigorous treatment would use a CNN-based
> estimator (Future Work).

**Q27. (1) If you had to extend this work to one new image domain
(satellite, medical CT, microscopy of plant cells), what changes?**
> Mainly the parameter sweep. The thresholds T_low and T_high are
> relative to σ²_n, which is portable. The Kirsch kernels are
> orientation-aware, so they generalise. The main failure mode is
> if the new domain has *spatially varying* noise — that's where
> the per-image parameter selection (Future Work) becomes
> necessary.

**Q28. (3) What if a panel member says "your AVGF is just a Box with
extra steps"?**
> Three counter-points:
> 1. AVGF's *per-pixel* σ is data-dependent; Box's is constant.
> 2. AVGF's EPI matches the median filter, Box's is below it.
> 3. AVGF has a tunable σ_min, σ_max — Box does not.
>
> The fact that the SSIM gain is modest is honest, not a flaw.

---

## 6 · Quick-fire definitions card (one-pager to glance over before
walking in)

| Term | One-liner |
|---|---|
| Convolution | Sliding-window sum-product with a kernel |
| Poisson noise | Photon-count randomness, variance = mean |
| Gaussian read noise | Camera electronics, mean 0, fixed σ |
| Box | Mean of 3×3 window |
| Median | Middle value of sorted 3×3 window |
| Sobel | Two 3×3 gradient kernels |
| Laplacian | 3×3 second-derivative, detects edge polarity |
| Unsharp mask | Original minus blurred, add back scaled |
| Kirsch compass | 8 rotated 3×3 gradient kernels |
| AVGF | Per-pixel Gaussian σ chosen by local variance |
| NGKCS | Kirsch responses blended by SNR gate |
| Immerkær | Noise variance estimator, no clean reference needed |
| MSE | Mean of squared pixel errors |
| PSNR | 20·log10(255/√MSE), in dB |
| SSIM | Structural similarity, three terms, range −1 to 1 |
| EPI | Edge Preservation Index, Sattar 1997 |
| Pratt FoM | Edge-localisation accuracy, Pratt 1978 |
| IoU | Intersection over Union on segmentation masks |
| Otsu | Single-threshold foreground/background segmentation |
| Canny | Multi-stage edge detector, one-pixel-wide edges |
| α (in noise model) | Photon count scale, lower = more noise |
| σ_read (in noise model) | Standard deviation of additive read noise |
| c_low, c_high | Multipliers of σ²_n that set AVGF's variance thresholds |
| k_0 | NGKCS sharpening strength (sweep best 0.3) |
| α (in NGKCS) | Gate steepness (sweep best 4.0) |
| N (in AVGF) | Number of pre-computed Gaussian levels (we used 4) |

---

## 7 · Common viva traps (don't fall into these)

- **"Box wins PSNR, so the project failed."** No — the standards are
  hard to beat; the contribution is in identifying *where* the custom
  designs recover. PO4 rewards honest investigation.
- **"AVGF is just a Box with bells and whistles."** No — per-pixel σ
  is fundamentally different from constant σ. The EPI matches the
  median, which a Box cannot do.
- **"We used median for SSIM because it's robust."** Almost right but
  tautological. Better: "Median is robust to outliers by construction
  (it's an order statistic), so a single noisy pixel cannot pull the
  output, which preserves edge transitions and the structure term of
  SSIM."
- **"Our custom filter is better than the standard ones."** Watch the
  word *better*. The report never says this. It says *competitive in
  specific regimes*. Use that phrase.
- **"We added two filters and they did X."** Watch the *we*. This
  is three-person work — credit the team.
- **"We don't know why Sobel does worse than noisy on PSNR."** You
  do. Sobel *adds* noise-edges to the image. PSNR penalises any
  pixel difference from clean.
- **"Pratt FoM is the best metric."** No metric is the best. Each
  measures something different. Pratt FoM is the right metric for
  edge-localisation tasks. PSNR is the right metric for
  full-image fidelity. Choose by the use case.

---

## 8 · Last-minute checklist (the night before)

- [ ] Open the report PDF and verify the table numbers on slide 13/15
      match — they should, but I have caught discrepancies before.
- [ ] Open the deck, click through all 17 slides, fix anything that
      looks off (overlapping subtitles, off-screen images).
- [ ] Read the speaker script at least twice aloud.
- [ ] Each team member should be able to answer Q1–Q6 and the
      questions marked with their number above (1/2/3).
- [ ] Time your rehearsal. Aim for 7-7.5 min to leave a 30-sec buffer
      for handoffs.
- [ ] Have `results/tables/all_results.csv` open in a tab in case the
      panel asks for a number you don't remember.
- [ ] Have the pipeline script `src/experiments/run_pipeline.py`
      open in a tab in case the panel asks how to reproduce.
- [ ] Don't drink too much coffee. Breathe.
