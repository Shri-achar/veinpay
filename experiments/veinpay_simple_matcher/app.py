"""Standalone experimental image matcher. Not a validated biometric authenticator."""
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import sqlite3

import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
REFS = DATA / 'references'
DB = DATA / 'references.sqlite3'
REFS.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
app.secret_key = 'local-demo-secret-change-before-exposing'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
ALLOWED = {'.jpg', '.jpeg', '.png', '.bmp'}


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute('CREATE TABLE IF NOT EXISTS refs (id TEXT PRIMARY KEY, label TEXT NOT NULL, filename TEXT NOT NULL, created TEXT NOT NULL)')


def read_image(upload):
    if not upload or not upload.filename or Path(secure_filename(upload.filename)).suffix.lower() not in ALLOWED:
        raise ValueError('Select a JPG, PNG, or BMP image.')
    payload = upload.read()
    if not payload or len(payload) > 8 * 1024 * 1024:
        raise ValueError('Image is empty or exceeds 8 MB.')
    frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None or min(frame.shape[:2]) < 80:
        raise ValueError('Image could not be decoded or is too small (minimum 80 × 80).')
    return frame


def process(frame):
    """Identical CLAHE preprocessing for both reference and query images.

    Full frame is retained. Existing black/white processed uploads also work,
    but never mix differently processed images for meaningful comparisons.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def similarity(a, b):
    """ORB BF-Hamming ratio plus evidence count. Heuristic, not a probability."""
    orb = cv2.ORB_create(nfeatures=1200)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 12 or len(kb) < 12:
        return None, 0, 0
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    good = sum(m.distance < 50 for m in matches)
    return (100.0 * good / len(matches) if matches else 0.0), len(matches), good


def all_refs():
    with sqlite3.connect(DB) as con:
        return con.execute('SELECT id, label, filename, created FROM refs ORDER BY created DESC').fetchall()


@app.route('/')
def index():
    return render_template('index.html', refs=all_refs(), results=None, threshold=None)


@app.route('/enroll', methods=['POST'])
def enroll():
    label = request.form.get('label', '').strip()
    if not label or len(label) > 80:
        flash('Enter a reference label (1–80 characters).', 'error')
        return redirect(url_for('index'))
    try:
        processed = process(read_image(request.files.get('image')))
        ref_id = 'VP-' + uuid4().hex[:10].upper()
        filename = ref_id + '.png'
        if not cv2.imwrite(str(REFS / filename), processed):
            raise ValueError('Unable to save processed image.')
        with sqlite3.connect(DB) as con:
            con.execute('INSERT INTO refs VALUES (?, ?, ?, ?)', (ref_id, label, filename, datetime.now(timezone.utc).isoformat()))
        flash(f'Saved {label} as {ref_id} (CLAHE processed).', 'success')
    except ValueError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('index'))


@app.route('/compare', methods=['POST'])
def compare():
    try:
        query = process(read_image(request.files.get('image')))
        # A user-set heuristic, useful for a demonstration only; requires calibration.
        threshold = float(request.form.get('threshold', '40'))
        if not 0 <= threshold <= 100:
            raise ValueError('Threshold must be between 0 and 100.')
        results = []
        for rid, label, name, _ in all_refs():
            saved = cv2.imread(str(REFS / name), cv2.IMREAD_GRAYSCALE)
            if saved is None:
                continue
            score, matches, good = similarity(query, saved)
            results.append({'id': rid, 'label': label, 'score': score, 'matches': matches, 'good': good})
        results.sort(key=lambda r: -1 if r['score'] is None else r['score'], reverse=True)
        best = results[0] if results else None
        # Require basic evidence and an unambiguous lead over second-ranked reference.
        runner = results[1] if len(results) > 1 else None
        outcome = 'INSUFFICIENT FEATURES' if best and (best['score'] is None or best['matches'] < 15 or best['good'] < 8) else (
            'POSSIBLE MATCH' if best and best['score'] >= threshold and (not runner or runner['score'] is None or best['score'] - runner['score'] >= 5)
            else 'NO RELIABLE MATCH')
        if not best:
            outcome = 'NO REFERENCES SAVED'
        return render_template('index.html', refs=all_refs(), results=results, best=best, outcome=outcome, threshold=threshold)
    except (ValueError, TypeError) as exc:
        flash(str(exc), 'error')
        return redirect(url_for('index'))


@app.route('/delete/<ref_id>', methods=['POST'])
def delete(ref_id):
    with sqlite3.connect(DB) as con:
        found = con.execute('SELECT filename FROM refs WHERE id=?', (ref_id,)).fetchone()
        if found:
            con.execute('DELETE FROM refs WHERE id=?', (ref_id,))
    if found:
        (REFS / found[0]).unlink(missing_ok=True)
        flash('Reference deleted.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5055, debug=False)
else:
    init_db()
