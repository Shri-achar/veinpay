# VeinPay V3 Improvement Roadmap

> **Status: planned and experimental.** This document records an improvement
> plan for VeinPay. It does not describe implemented V3 functionality, nor does
> it claim validated recognition performance. The existing V2 code and profiles
> should be preserved while experiments are performed separately.

## Current V2 pipeline

The present pipeline is understood to use the following stages:

1. Capture a near-infrared palm image.
2. Crop a central, non-anatomical ROI. The earlier project report describes a
   central 85% crop, while the current `processing/preprocess.py` code crops
   15% from every edge (a central 70% ROI). This discrepancy must be resolved
   and recorded for each experiment.
3. Apply CLAHE contrast enhancement and Gaussian smoothing.
4. Apply Frangi vesselness filtering.
5. Extract and match ORB features.
6. Rank candidate identities using multiple enrolled templates.

This is a useful experimental baseline, but it has not yet been validated as a
reliable biometric-recognition pipeline.

## Known limitations to investigate

- Neither the report's central 85% crop nor the current code's central 70% crop
  is an anatomical palm ROI. Hand position, rotation, distance, and framing can
  therefore change the tissue represented in the ROI.
- Gaussian smoothing may suppress fine vein detail along with sensor noise.
- ORB keypoints can correspond to wrinkles, shadows, edges, or other
  nonvascular structures rather than vein patterns.
- An empty or poor-quality frame may still produce a plausible candidate unless
  palm presence and image-quality checks reject it first.
- Current similarity/ranking scores are uncalibrated. They should not be treated
  as confidence values or used for a production accept/reject decision without
  genuine/impostor evaluation and threshold selection.

## V3 experiments (planned; not implemented or validated)

V3 should be developed in a separate branch or workspace and compared with V2;
do not overwrite existing V2 profiles during these experiments.

### 1. Validate input and image quality

- Add a hand/palm-presence check before feature extraction.
- Define quality checks for focus, exposure, illumination uniformity, usable
  palm coverage, and excessive motion/blur.
- Reject empty, occluded, badly framed, or low-quality frames with an explicit
  reason rather than returning a ranked identity.

### 2. Establish an anatomical ROI and alignment method

- Evaluate palm/hand segmentation and stable hand landmarks (for example,
  finger-valley geometry) to locate an anatomical ROI.
- Normalize rotation, scale, and translation before comparing samples.
- Save ROI overlays and alignment diagnostics for inspection; do not assume a
  crop is correct solely because matching returns a result.

### 3. Run preprocessing ablations

- Compare the current CLAHE, smoothing, and Frangi steps independently and in
  combinations.
- Test whether reducing or omitting Gaussian smoothing preserves useful fine
  vein structure without making matching too noise-sensitive.
- Keep experiment settings, inputs, and outcomes versioned so changes are
  attributable and reproducible.

### 4. Compare feature and matcher baselines

- **Candidate vascular baseline:** evaluate Gabor/Competitive Code features
  with masked, normalized Hamming distance. This is a proposed comparison
  baseline, not an implemented or approved replacement.
- Retain ORB as a comparison baseline, rather than assuming it is the final
  matcher.
- Evaluate SuperPoint + LightGlue only as an additional comparison baseline,
  subject to Raspberry Pi feasibility and the same evaluation protocol.
- Record whether features visually correspond to stable vascular structure;
  avoid selecting a method based only on a small number of successful matches.

### 5. Make multi-template matching robust

- Store several enrollment samples per identity captured across small natural
  repositioning changes.
- Evaluate aggregation rules such as top-k mean, median, or quality-weighted
  template scores instead of relying on one best matching template.
- Separately log the top candidate, competing candidate scores, and rejection
  decision for later analysis.

### 6. Evaluate before claiming improvement

- Build a subject-disjoint protocol with separate enrollment and test captures.
- Collect both genuine comparisons and impostor comparisons.
- Report false-accept rate (FAR), false-reject rate (FRR), equal-error rate
  (EER), and identification Rank-1 accuracy where the data supports them.
- Choose any decision threshold from held-out validation data, then report final
  results on unseen test data. Do not report confidence or improved performance
  until this evaluation is complete.

## Tomorrow's focused work plan (10:00 AM–5:00 PM)

### 10:00–10:30 — Protect V2 and map the pipeline

- [ ] Back up the current V2 project.
- [ ] Create a separate `VeinPay_V3` branch or workspace.
- [ ] Identify the files responsible for preprocessing, Frangi filtering, ORB,
  enrollment, recognition, and score/ranking logic.

### 10:30–11:30 — Collect and inspect representative images

- [ ] Capture five enrollment and five test images for each of at least five
  people, with small natural repositioning between captures.
- [ ] Keep distance and illumination as consistent as practical.
- [ ] Preserve original images separately from derived ROIs and processed data.
- [ ] Review visibility of veins, shadows, focus, exposure, illumination, and
  wrinkles.

### 11:30–12:15 — Design ROI diagnostics

- [ ] Capture sample frames showing expected hand placement variation.
- [ ] Prototype or document an anatomical landmark/segmentation approach.
- [ ] Produce visual ROI overlays for manual review; do not replace V2 yet.

### 12:15–1:00 — Define validation and rejection checks

- [ ] Write initial palm-presence and quality rules.
- [ ] Gather examples of empty, blurred, misframed, and over/underexposed
  frames for testing.
- [ ] Decide what the application should display when a frame is rejected.

### 1:00–1:30 — Break

- [ ] Pause before changing the algorithm; keep notes and data organized.

### 1:30–2:30 — Establish the evaluation harness

- [ ] Separate enrollment and test captures by person and session.
- [ ] Generate genuine and impostor comparison lists.
- [ ] Add logging for score distributions, candidate rankings, and rejection
  reasons.

### 2:30–3:30 — Preprocessing ablation setup

- [ ] Run the existing V2 preprocessing on the fixed dataset.
- [ ] Set up controlled variants for CLAHE, Gaussian smoothing, and Frangi.
- [ ] Save visual outputs and measurements for each variant.

### 3:30–4:30 — Baseline comparison setup

- [ ] Run and document V2 ORB results as a baseline.
- [ ] Specify the planned Gabor/Competitive Code masked normalized-Hamming
  experiment without presenting it as implemented.
- [ ] Assess whether a SuperPoint + LightGlue comparison is feasible before
  adding dependencies or changing the deployed system.

### 4:30–5:00 — Review and decide the next experiment

- [ ] Inspect failures rather than selecting a matcher from a few successes.
- [ ] Summarize data quality, ROI stability, and genuine/impostor score overlap.
- [ ] Choose one controlled V3 experiment for the next session.

## Documentation discipline

For each experiment, record the dataset version, capture conditions, code
revision, configuration, preprocessing choices, matcher, aggregation rule,
threshold method, and evaluation results. Label incomplete, exploratory, and
unvalidated work clearly.

