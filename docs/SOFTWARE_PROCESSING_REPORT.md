> **Report status (November 2026):** This is a project report supplied by the team and is preserved as project documentation. It contains reported and experimental configurations that have not all been independently verified against the current `main` branch. In particular, the checked-in core preprocessing code currently uses a central 70% crop (15% removed from each edge), while this report describes an 85% crop. Treat source code and the experiment logs as the authoritative implementation record until a fresh audit reconciles these differences. This report does not validate biometric performance or authorize payment use.

# VeinPay — Complete Software Processing and Algorithm Report

**Project:** VeinPay — Contactless Palm-Vein Recognition and Simulated Payment System  
**Platform:** Raspberry Pi 5  
**Camera:** Raspberry Pi Camera Module 3 NoIR (IMX708)  
**Framework:** Python, OpenCV, scikit-image, Flask  
**Pipeline:** Palm Image Acquisition → ROI Extraction → Image Enhancement → Frangi Vesselness → Feature Extraction → Template Matching → Candidate Identification

---

## 1. Project Overview

VeinPay is a contactless biometric prototype designed to recognize individuals using near-infrared (NIR) images of their palm vascular patterns.

The system captures palm images through an infrared-sensitive camera, enhances the visible vessel-like structures using image-processing algorithms, and compares the resulting features with previously registered templates.

The project consists of two primary software workflows:

1. **Enrollment:** Capturing and processing palm images to create reference templates for each user.
2. **Recognition:** Capturing a new palm image and comparing its features with previously registered users.

The main dashboard uses a conventional computer-vision pipeline based on CLAHE, Gaussian filtering, Frangi vesselness enhancement and ORB feature matching.

The system currently provides experimental identity-matching results. Matching scores have not been calibrated as identity probabilities, and biometric payment authorization remains experimental or disabled.

## 2. Overall Software Architecture

```text
              RASPBERRY PI CAMERA
                      |
                Raw NIR Frame
                      |
             Central 85% × 85% ROI
                      |
             Grayscale Conversion
                      |
                CLAHE (2.0)
                      |
            Gaussian Noise Reduction
                      |
             Additional Blur (5.1)
                      |
             Frangi Vesselness Filter
                      |
            Normalized Frangi Image
                      |
               ORB Feature Extraction
                      |
             Feature Correspondence
                      |
           Candidate Template Matching
                      |
           Multi-Template Verification
                      |
            Best Candidate + Scores
                      |
              FLASK WEB DASHBOARD
```

The pipeline is implemented primarily in Python, while Flask handles the dashboard interface and communication between the browser and Raspberry Pi.

## 3. Stage 1 — Palm Image Acquisition

### Hardware

The system uses the Raspberry Pi Camera Module 3 NoIR, which does not have the conventional infrared-cut filter found in regular visible-light camera modules.

Its sensor can therefore capture near-infrared illumination reflected from the palm.

### Illumination

The currently documented setup uses SmartElex RLS08 infrared illuminator boards emitting approximately 950 nm light, together with additional infrared LEDs.

The camera records reflected NIR intensity from the palm.

Blood vessels can appear darker than surrounding tissue because of wavelength-dependent optical absorption and scattering, including absorption by haemoglobin.

Vein contrast also depends on camera sensitivity, illumination intensity, tissue properties, distance, angle, exposure and focus.

### Acquisition software

The Raspberry Pi camera subsystem captures frames, which are provided to the Python image-processing and dashboard software.

OpenCV is used for subsequent image operations.

The exact camera capture interface, pixel format and whether any intermediate JPEG encoding occurs should be checked in the current camera source code.

### Output

A captured camera frame is supplied to the preprocessing pipeline.

**Important:** Illumination quality is determined during this stage. Preprocessing cannot reliably reconstruct vascular information that was not captured.

## 4. Stage 2 — Region of Interest (ROI) Extraction

**Algorithm:** Centered rectangular ROI cropping

The current standardized enrollment and recognition pipeline uses the central 85% of the frame width and 85% of the frame height.

For a 1280 × 720 camera frame:

| Parameter | Value |
|---|---:|
| Original width | 1280 px |
| Original height | 720 px |
| ROI width | 1088 px |
| ROI height | 612 px |
| Left/right margins | 96 px |
| Top/bottom margins | 54 px |

The ROI excludes the outermost image areas to reduce irrelevant background information.

The dashboard displays green positioning guides corresponding to the intended capture region.

### Purpose

- Improve consistency between enrollment and live scans.
- Exclude some peripheral background information.
- Concentrate feature extraction on the central palm area.
- Reduce sensitivity to objects near the image boundaries.

### Limitation

The current centered crop is not an anatomical palm-segmentation algorithm.

It does not automatically identify the palm boundary or guarantee that the entire ROI contains hand tissue. Background textures can remain inside the ROI.

Legacy enrollment profiles may use older ROI configurations, but new v2 enrollments use the standardized 85% ROI.

## 5. Stage 3 — Grayscale Conversion

**Algorithm:** BGR-to-grayscale conversion

OpenCV converts the camera frame into a single-channel grayscale image.

```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

Each pixel represents image intensity instead of three separate color channels.

### Purpose

- Reduce processing complexity.
- Prepare the image for contrast enhancement.
- Provide a single-channel input to Frangi filtering.
- Focus subsequent processing on local intensity variations.

Because the camera is being used for near-infrared imaging, the intensity pattern is more relevant than conventional visible color.

## 6. Stage 4 — CLAHE Contrast Enhancement

**Algorithm:** Contrast Limited Adaptive Histogram Equalization (CLAHE)

CLAHE enhances local image contrast by dividing the image into regions and adjusting their intensity distributions.

Unlike ordinary global histogram equalization, CLAHE works locally and limits excessive contrast amplification.

### Current settings

| Parameter | Value |
|---|---:|
| Clip limit | 2.0 |
| Tile grid size | 8 × 8 |

Conceptual OpenCV implementation:

```python
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)
enhanced = clahe.apply(gray)
```

### Purpose

- Enhance subtle differences between vessel regions and surrounding tissue.
- Improve contrast in locally low-contrast parts of the palm.
- Reduce the need for extreme global contrast changes.

### Limitation

CLAHE does not distinguish true veins from other dark structures.

It can also enhance surface wrinkles, shadows, image noise and illumination artifacts.

Increasing the clip limit does not increase infrared penetration.

## 7. Stage 5 — Gaussian Noise Reduction

**Algorithm:** Gaussian Blur / Gaussian Smoothing

Gaussian filtering smooths local intensity variations and suppresses high-frequency noise.

The current preprocessing profile includes:

- Base Gaussian filtering with a 3 × 3 kernel.
- Additional Gaussian smoothing corresponding to a 51% blur setting.
- Additional Gaussian sigma approximately 5.1.

A Gaussian kernel gives greater weight to nearby pixels and progressively smaller weights to more distant pixels.

### Purpose

- Reduce sensor noise.
- Suppress small unwanted intensity fluctuations.
- Produce a smoother input for Frangi vesselness filtering.
- Improve continuity of certain vessel-like structures.

### Limitation

Excessive Gaussian smoothing can remove thin veins or merge nearby structures.

The current settings were selected through experimental visual comparisons. They are not yet proven optimal for all users.

## 8. Stage 6 — Frangi Vesselness Enhancement

**Algorithm:** Multiscale Frangi Vesselness Filter

This is one of the most important algorithms in VeinPay.

Frangi filtering enhances image structures that resemble elongated blood vessels.

It uses the Hessian matrix, which represents local second-order intensity changes.

For a two-dimensional image, the Hessian is:

\[
H =
\begin{bmatrix}
I_{xx} & I_{xy}\\
I_{xy} & I_{yy}
\end{bmatrix}
\]

The eigenvalues of this matrix describe how intensity changes in different local directions.

By analyzing eigenvalue relationships, the Frangi filter estimates whether an image region resembles a line or ridge.

The filter is applied over multiple spatial scales to detect structures of different apparent widths.

### Current Frangi v2 settings

| Parameter | Value |
|---|---|
| Sigma scales | 1, 2, 3, 4 |
| Maximum sigma setting | 5 (exclusive) |
| Alpha | 0.50 |
| Beta | 0.50 |
| Gamma | Automatic |
| Ridge polarity | Dark ridges |
| Input | uint8 grayscale after preprocessing |
| Float32 / 255 tuner conversion | Disabled |

### Purpose

- Enhance elongated, vein-like patterns.
- Suppress some non-line-shaped image content.
- Extract vesselness information at multiple scales.
- Provide an enhanced image for feature matching.

### Output

The vesselness response is normalized into an 8-bit grayscale image.

The principal matching-related output is:

`05_frangi.png`

### Important limitation

Frangi does **not** confirm that an enhanced line is anatomically a blood vessel.

Skin creases, wrinkles, shadows and background edges may also produce strong vesselness responses.

Therefore, a visually detailed Frangi output is not automatically proof of successful vein extraction.

## 9. Stage 7 — Binary Thresholding

**Algorithm:** Binary Image Thresholding

The current v2 profile uses a binary threshold value of 10 for generating the visual binary output.

Conceptually:

```python
_, binary = cv2.threshold(
    frangi_image,
    10,
    255,
    cv2.THRESH_BINARY
)
```

### Output

`06_binary.png`

### Purpose

- Visualize enhanced structures as white foreground lines against a black background.
- Support inspection of the image-enhancement process.
- Provide a simplified representation of the vesselness output.

**Important:** Threshold 10 is a preprocessing visualization threshold, not an authentication threshold.

The current documented feature-selection and matching flow uses the normalized grayscale Frangi representation, rather than relying solely on this binary image.

## 10. Enrollment Workflow

During enrollment, the system captures multiple images of a registered user's palm.

The current process uses ten enrollment samples.

Each sample is processed through the standardized Frangi v2 pipeline.

### Saved processing stages

| File | Description |
|---|---|
| `00_original.png` | Original captured frame |
| `01_roi.png` | Central ROI |
| `02_gray.png` | Grayscale image |
| `03_clahe.png` | Locally enhanced contrast |
| `04_blurred.png` | Smoothed Frangi input |
| `05_frangi.png` | Normalized Frangi vesselness |
| `06_binary.png` | Thresholded vesselness |

These images help trace how each processing stage changes the captured image.

### Enrollment profile

The current profile is identified as:

`palm-frangi-roi85-v2`

Enrollment metadata records preprocessing settings and relevant file hashes so that subsequent recognition can use a compatible processing configuration.

## 11. Enrollment Template Selection

**Algorithm:** Laplacian Variance-Based Sharpness Ranking

The system calculates an image-quality score from the Frangi output using the variance of the Laplacian response.

\[
Q = \operatorname{Var}(\nabla^2 I)
\]

Where:

- \(I\) is the processed image.
- \(\nabla^2 I\) is the Laplacian response.
- \(Q\) is a sharpness-related score.

Images with stronger local intensity transitions generally receive higher scores.

### Selection process

1. Process all ten enrollment images.
2. Calculate the Laplacian variance of each Frangi image.
3. Sort the samples by their scores.
4. Select the highest-ranked image as the primary template.
5. Retain additional highly ranked reference templates.

For User 52, the documented selection ranked Sample 09 first, followed by Samples 05 and 06.

The primary reference is stored as a versioned template, including the file:

`template_roi85_v2.png`

### Limitation

Laplacian variance measures image sharpness-related properties.

It does not prove that a particular image contains the most genuine veins, nor does it measure whether vein branches repeat consistently across captures.

## 12. Live Scan and Recognition

When the user clicks **Scan & Identify**, the application captures a fresh image and processes it using the compatible enrollment preprocessing profile.

The live-processing stages follow the same general sequence:

1. Camera capture.
2. ROI cropping.
3. Grayscale conversion.
4. CLAHE.
5. Gaussian filtering.
6. Frangi vesselness.
7. Feature extraction.
8. Database template comparison.

Maintaining compatible enrollment and live preprocessing is important.

If one image is cropped or enhanced differently from its reference template, feature correspondences may change even when the same person is scanned.

## 13. ORB Feature Extraction

**Algorithm:** Oriented FAST and Rotated BRIEF (ORB)

The main recognition pipeline uses ORB to extract and describe local image features.

ORB combines two important techniques:

**FAST — Features from Accelerated Segment Test**

Detects distinctive local points based on surrounding intensity differences.

**BRIEF — Binary Robust Independent Elementary Features**

Produces compact binary descriptors describing the intensity relationships around detected feature points.

ORB adds orientation handling and is designed to support efficient local feature matching.

### Why ORB was chosen

- Computationally efficient.
- Suitable for Raspberry Pi execution.
- Produces compact binary descriptors.
- Can tolerate some changes in position and rotation.
- Does not require training a large neural network.

### Important distinction

ORB is not itself a vein detector.

It describes visually distinctive structures in the image supplied to it.

When applied to Frangi images, those structures may include enhanced vessel-like lines but can also include other image features.

## 14. Feature Matching

**Algorithm family:** Binary descriptor correspondence matching

After ORB descriptor extraction, the system compares descriptors from the live image against those from enrolled templates.

ORB binary descriptors are commonly compared using Hamming distance, which measures differences between descriptor bits.

The matching stage identifies local feature correspondences between the two images.

The documented project also includes matching logic for evaluating candidate quality and multiple reference images.

### General process

```text
Live Frangi image
       |
   ORB descriptors
       |
Compare with enrolled
template descriptors
       |
Evaluate feature correspondences
       |
Rank matching candidates
```

The exact current scoring formula and acceptance conditions are defined in the project recognition code and must be checked before quoting a specific percentage as an official acceptance threshold.

## 15. Candidate Identification

The application evaluates similarity between the live palm representation and registered reference templates.

It then identifies the strongest candidate according to the current matching score.

The main dashboard can display:

- Best matching candidate.
- Registered name.
- User ID.
- Original ORB similarity score.
- Multi-template scores.
- Additional diagnostic information.

### Important observation

A *best matching candidate* is simply the highest-ranked entry among the evaluated templates.

It does not automatically mean that the scan is a genuine match.

For example, if the camera captures an empty background and the recognition code does not reject it beforehand, the matching procedure may still produce a highest-ranked user from background-related feature correspondences.

That is the issue recently observed in our dashboard.

## 16. Multi-Template Matching

**Algorithm:** Multi-Reference Template Evaluation

Instead of relying exclusively on a single enrollment template, the project includes a multi-template matching stage.

The documented implementation can evaluate up to ten enrollment samples associated with a candidate user.

It reports metrics including:

- **Top-3 similarity:** A score based on leading enrollment-template comparisons.
- **MAX similarity:** The highest observed reference-template similarity.
- **Best matching enrollment sample:** The reference image yielding the strongest result.

### Purpose

Palm position, illumination, focus and other acquisition conditions may vary between scans.

Multiple reference templates provide additional opportunities to find useful feature correspondences.

For example, one enrollment image may contain stronger vessel-like features in one region, while another may have better illumination or positioning.

### Limitation

A maximum-score strategy can also select an accidentally high impostor or background match. Multi-template matching must therefore be evaluated against wrong-user comparisons, not just genuine matches.

The documented user-53 test previously produced an original ORB score of 81.64%, Top-3 score of 85.71% and MAX score of 88.12%.

These are experimental similarity outputs, not probabilities of identity correctness.

## 17. Final Result Logic

The main dashboard reports the strongest candidate and experimental matching measurements.

It is important to separate three concepts:

**Candidate ranking:** Which registered user most closely resembles the input according to the algorithm?

**Match acceptance:** Does the score satisfy a validated decision rule?

**Payment authorization:** Is the system sufficiently reliable and secure to permit a real financial transaction?

The current documented system supports experimental candidate ranking and comparison.

Its scores must not be treated as validated biometric authentication probabilities.

### Empty-frame problem

A recent test showed that the system could display a registered candidate even when no hand was visible.

This indicates the need for a verified input-validity mechanism before accepting identification results.

A proposed conservative hand-presence check is still experimental; its successful integration and rollback status have not been verified here.

Therefore, the report does not assume that the no-hand rejection improvement is already implemented.

## 18. Recognition Comparison — Separate Experimental Pipeline

VeinPay also contains a separate Recognition Comparison interface.

That experimental workflow includes:

**SuperPoint:** A learned feature-point detector and descriptor.

**LightGlue:** A learned feature matcher that estimates correspondences between image features.

The documented comparison interface can use palm grayscale imagery with SuperPoint and LightGlue instead of the conventional Frangi-plus-ORB recognition path.

Its experimental visual decision logic previously required:

- Correspondence score strictly greater than 45%.
- A valid geometric consistency check.

Failure of the geometry check produces an inconclusive result.

This interface is for comparative research and should not be confused with the main dashboard's matching implementation.

It does not provide real payment authorization.

## 19. Web Dashboard and Backend

**Framework:** Flask

Flask connects the browser interface with the Raspberry Pi's camera and recognition software.

The system includes routes for:

| Interface | Purpose |
|---|---|
| Main dashboard `/` | System overview |
| `/enroll` | Register users and capture enrollment samples |
| `/scan` | Palm scanning and experimental identification |
| `/payment` | Simulated payment workflow |
| `/merchant-wallet` | Merchant wallet interface |
| `/frangi-lab/` | Interactive preprocessing experiments |
| `/recognition-comparison/` | Experimental matcher comparison |

The Frangi Lab allows developers to experiment with preprocessing settings without automatically treating every configuration as a new production standard.

### Starting the application

From the project root:

```bash
cd /home/tanushc/VeinPay
/usr/bin/python3 dashboard/app.py
```

The Flask service uses port 5000 in the documented setup.

## 20. Main Algorithms Used

| Stage | Algorithm / technology | Primary purpose |
|---|---|---|
| Camera | Raspberry Pi NoIR imaging | Capture reflected NIR light |
| ROI | Centered cropping | Focus on the palm region |
| Color conversion | OpenCV grayscale | Simplify intensity analysis |
| Contrast enhancement | CLAHE | Improve local contrast |
| Noise filtering | Gaussian smoothing | Reduce noise |
| Vein enhancement | Frangi vesselness | Highlight elongated structures |
| Binary visualization | Thresholding | Display enhanced line patterns |
| Template ranking | Laplacian variance | Rank image sharpness |
| Feature detection | ORB / FAST | Detect distinctive points |
| Feature description | ORB / rotated BRIEF | Describe local features |
| Feature comparison | Binary descriptor matching | Find correspondences |
| Recognition | Candidate ranking | Identify strongest candidate |
| Template verification | Multi-template comparison | Compare multiple captures |
| Experimental matcher | SuperPoint + LightGlue | Alternative learned correspondence |
| Web application | Flask | Dashboard and backend communication |
| Storage | SQLite + image files | User records and templates |

## 21. Current Strengths

- Contactless palm scanning.
- Raspberry Pi-based local operation.
- Versioned and consistent preprocessing.
- Normalized grayscale Frangi templates.
- Multiple enrollment samples per user.
- Computationally efficient conventional feature matching.
- Separate experimentation through Frangi Lab and Recognition Comparison.
- Improved recognition observations after the Frangi v2 update.

## 22. Current Technical Limitations

1. Vein visibility varies between individuals under the present IR illumination.
2. The camera's 950 nm response and imaging configuration may not be optimal for all palms.
3. The fixed centered ROI is not a true hand-segmentation method.
4. Frangi may enhance wrinkles, shadows and other nonvascular structures.
5. Sharpness-based enrollment selection does not guarantee genuine vessel repeatability.
6. Empty or background-only frames can produce misleading candidate rankings without sufficient input checks.
7. Experimental similarity scores have not been validated as secure biometric authentication measures.
8. The system needs a larger controlled test dataset covering repeated scans, different users and varied imaging conditions.

## 23. Future Research and Improvement

Recommended directions include:

- Controlled comparison of 850 nm and 950 nm illumination.
- Optimized illumination angle and diffusion.
- Camera exposure and gain calibration.
- Improved suppression of background reflections.
- Reliable palm-presence and input-quality detection.
- More robust palm localization and alignment.
- Selection of enrollment templates based on repeatable features.
- Evaluation using genuine and impostor comparisons.
- Calibration of recognition decision thresholds.
- Investigation of learned vein representations only after acquiring suitable training data.

All experimental improvements should preserve the current working enrollment and recognition profiles until their performance is independently verified.

## 24. Conclusion

VeinPay implements a multi-stage palm-vein recognition pipeline combining near-infrared image acquisition, local contrast enhancement, multiscale vesselness filtering and feature-based biometric comparison.

The principal conventional algorithms are **CLAHE, Gaussian Blur, Frangi Vesselness, Laplacian Variance and ORB feature matching**, supported by multiple enrollment templates.

The current system is capable of extracting and comparing vein-like structures from suitable NIR palm images, with promising results observed for selected registered users.

The primary remaining challenges are obtaining consistent vascular contrast across different individuals, ensuring that matched features originate from meaningful palm information, rejecting invalid captures and validating the recognition decision process.

VeinPay remains an experimental biometric payment prototype rather than a production-validated payment authentication system.

---

**Report basis:** Documented VeinPay implementation and experimental results through November 2026. Exact current source-code branches, matcher score formulas and recently proposed changes require a fresh read-only audit before this is used as a final code-verified implementation specification.
