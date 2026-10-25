# Experiments and results

Data: 10 enrolled left-palm images (one user). Test set of 15 held-out images: genuine left palm
from two sessions, 3 fixed-focus captures, the same person's unenrolled right palm, and a different
person's left palm. Scores are a heuristic (% of cross-checked ORB matches with Hamming distance < 50,
mean of the best 3 references), **not** a confidence probability.

## Methods compared (`experiments/palm_algorithm_comparison.py`)

| Method | ROI | Processing |
|---|---|---|
| OLD_FRANGI | x 18-72%, y 18-82% | CLAHE 3.0, Frangi sigma 1-5 |
| CURRENT_FRANGI | centre 70% | CLAHE 2.0, blur, Frangi sigma 1-4 |
| CLAHE_ORB | centre 70% | CLAHE only |

## Findings

| Method | Autofocus mean | Fixed-focus mean | Genuine-vs-impostor gap |
|---|---:|---:|---:|
| OLD_FRANGI | 10.34% | 17.46% | -18.73 pts |
| CURRENT_FRANGI | 28.77% | 40.14% | -18.10 pts |
| CLAHE_ORB | 11.82% | 14.16% | -20.07 pts |

A negative gap means the best impostor scored higher than the worst genuine scan, so no safe
threshold exists with the current data. Fixing the lens position raised scores, but sessions also
differed in lighting and pose, so focus is not proven as the cause.

Other attempts that did not help: MobileNetV2 embeddings, MediaPipe hand landmarks (0/6 detected on
cropped palms), background subtraction, GrabCut, ECC alignment.

## Conclusions and next steps

- Frangi output does not prove subcutaneous veins are visible. Optics and pose need to be fixed first
  (distance calibration, a bandpass filter, a matte background, consistent hand placement).
- Test full-frame vs centre-crop with identical preprocessing for enrollment and scan.
- Collect more subjects and sessions before claiming any FAR/FRR.
- `experiments/veinpay_simple_matcher/` is an upload-only Flask tool for quick comparisons.
