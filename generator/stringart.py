#!/usr/bin/env python3
"""
stringart.py — turn a photo into a nail sequence for circular string art.

Greedy algorithm (the Vrellis / kmmeerts / halfmonty lineage):
  1. grayscale -> square crop -> resize -> circular mask -> invert (dark = high)
  2. N nails evenly spaced on the circle, nail 0 at 12 o'clock, clockwise
  3. precompute the pixels crossed by every chord (N*(N-1)/2 of them)
  4. from the current nail, score every allowed chord by the residual darkness
     it would cover, pick the best, subtract LINE_WEIGHT along it, repeat

Outputs (in --out-dir, named after the input file unless --name given):
  <name>.json   machine input: nails, hoop diameter, ordered nail sequence, thread length
  <name>.txt    one nail index per line (for winding by hand)
  <name>.png    rendered preview

Usage:
  python stringart.py samples/lincoln.jpg
  python stringart.py photo.jpg --nails 256 --lines 3500 --line-weight 18
"""

import argparse
import json
import os
import sys
import time
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageOps


# ----------------------------------------------------------------------------
# image preparation
# ----------------------------------------------------------------------------

def load_image(path: str, size: int, gamma: float, autocontrast: bool) -> np.ndarray:
    """Return a float32 array (size x size), 0 = white, 255 = black, masked to a circle."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("L")
    if autocontrast:
        img = ImageOps.autocontrast(img, cutoff=1)
    # centre crop to square
    w, h = img.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    img = img.crop((left, top, left + s, top + s))
    img = img.resize((size, size), Image.LANCZOS)

    a = np.asarray(img, dtype=np.float32)
    if gamma != 1.0:
        a = 255.0 * (a / 255.0) ** gamma
    residual = 255.0 - a  # dark pixels become high values

    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2.0
    r = size / 2.0
    outside = (xx - c) ** 2 + (yy - c) ** 2 > r * r
    residual[outside] = 0.0
    return residual


# ----------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------

def nail_positions(n: int, size: int) -> np.ndarray:
    """(n, 2) float array of (x, y) pixel positions. Nail 0 at top, clockwise on screen."""
    c = (size - 1) / 2.0
    r = size / 2.0 - 1.0
    i = np.arange(n)
    theta = -np.pi / 2.0 + 2.0 * np.pi * i / n
    x = c + r * np.cos(theta)
    y = c + r * np.sin(theta)  # image y grows downward, so this is clockwise on screen
    return np.stack([x, y], axis=1)


def chord_pixels(p0: np.ndarray, p1: np.ndarray, size: int) -> np.ndarray:
    """Flat pixel indices crossed by the segment p0 -> p1 (rounded linspace, ~Bresenham)."""
    length = int(np.hypot(*(p1 - p0)))
    n = max(length, 2)
    xs = np.rint(np.linspace(p0[0], p1[0], n)).astype(np.int32)
    ys = np.rint(np.linspace(p0[1], p1[1], n)).astype(np.int32)
    flat = ys * size + xs
    return np.unique(flat)


def build_chord_table(n: int, size: int, cache_dir: str | None):
    """
    Returns (idx, seg, lengths):
      idx[i]     int32 array: concatenated pixel indices of every chord i -> j (j != i)
      seg[i]     int32 array: same length as idx[i], the j each pixel belongs to
      lengths    (n, n) float32 array of chord lengths in pixels
    Cached to disk keyed on (n, size).
    """
    cache_path = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"chords_n{n}_s{size}.npz")
        if os.path.exists(cache_path):
            z = np.load(cache_path)
            idx = [z[f"idx{i}"] for i in range(n)]
            seg = [z[f"seg{i}"] for i in range(n)]
            return idx, seg, z["lengths"]

    pos = nail_positions(n, size)
    lengths = np.zeros((n, n), dtype=np.float32)
    pair = {}
    for i in range(n):
        for j in range(i + 1, n):
            px = chord_pixels(pos[i], pos[j], size)
            pair[(i, j)] = px
            lengths[i, j] = lengths[j, i] = float(np.hypot(*(pos[j] - pos[i])))

    idx, seg = [], []
    for i in range(n):
        parts, segs = [], []
        for j in range(n):
            if j == i:
                continue
            px = pair[(i, j)] if i < j else pair[(j, i)]
            parts.append(px)
            segs.append(np.full(px.shape[0], j, dtype=np.int32))
        idx.append(np.concatenate(parts))
        seg.append(np.concatenate(segs))

    if cache_path:
        payload = {"lengths": lengths}
        for i in range(n):
            payload[f"idx{i}"] = idx[i]
            payload[f"seg{i}"] = seg[i]
        np.savez_compressed(cache_path, **payload)
    return idx, seg, lengths


# ----------------------------------------------------------------------------
# greedy solver
# ----------------------------------------------------------------------------

def solve(residual: np.ndarray, n: int, lines: int, min_distance: int, min_loop: int,
          line_weight: float, score: str, start: int, idx, seg, lengths, verbose=True):
    size = residual.shape[0]
    res = residual.reshape(-1).copy()

    # per-chord pixel counts, for mean scoring
    counts = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        counts[i] = np.bincount(seg[i], minlength=n)
    counts[counts == 0] = 1.0

    # circular nail distance, for the min_distance rule
    ii, jj = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    d = np.abs(ii - jj)
    circ = np.minimum(d, n - d)
    too_close = circ < min_distance

    seq = [start]
    cur = start
    recent = deque(maxlen=max(min_loop, 1))
    recent.append(start)
    used_pairs = set()
    t0 = time.time()

    for step in range(lines):
        gain = np.bincount(seg[cur], weights=res[idx[cur]], minlength=n)
        if score == "mean":
            gain = gain / counts[cur]
        gain[cur] = -1.0
        gain[too_close[cur]] = -1.0
        for r in recent:
            gain[r] = -1.0
        # never draw the exact same chord twice
        for j in np.flatnonzero(gain > 0):
            if (min(cur, j), max(cur, j)) in used_pairs:
                gain[j] = -1.0

        nxt = int(np.argmax(gain))
        if gain[nxt] <= 0:
            if verbose:
                print(f"  stopped early at {step} lines: no chord adds darkness", file=sys.stderr)
            break

        m = seg[cur] == nxt
        px = idx[cur][m]
        res[px] = np.maximum(res[px] - line_weight, 0.0)

        used_pairs.add((min(cur, nxt), max(cur, nxt)))
        seq.append(nxt)
        recent.append(nxt)
        cur = nxt

        if verbose and (step + 1) % 500 == 0:
            print(f"  {step + 1}/{lines} lines, {time.time() - t0:.1f}s", file=sys.stderr)

    return seq, res.reshape(size, size)


# ----------------------------------------------------------------------------
# outputs
# ----------------------------------------------------------------------------

def thread_length_m(seq, lengths, size, hoop_diameter_m) -> float:
    px = sum(float(lengths[a, b]) for a, b in zip(seq[:-1], seq[1:]))
    return px * hoop_diameter_m / size


def render_fast(seq, n: int, out_size: int, scale: int = 4) -> Image.Image:
    """Opaque thin lines at high resolution, downsampled: fast and good enough for previews."""
    big = out_size * scale
    canvas = Image.new("L", (big, big), 255)
    draw = ImageDraw.Draw(canvas)
    pos = nail_positions(n, big)
    for a, b in zip(seq[:-1], seq[1:]):
        draw.line([tuple(pos[a]), tuple(pos[b])], fill=0, width=1)
    return canvas.resize((out_size, out_size), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--nails", type=int, default=288, help="number of nails on the hoop")
    ap.add_argument("--lines", type=int, default=4000, help="max number of chords")
    ap.add_argument("--min-distance", type=int, default=20, help="min nail-index gap for a chord")
    ap.add_argument("--min-loop", type=int, default=20, help="do not revisit the last K nails")
    ap.add_argument("--line-weight", type=float, default=15.0, help="darkness (0-255) removed per chord")
    ap.add_argument("--size", type=int, default=500, help="working image size in px")
    ap.add_argument("--score", choices=["sum", "mean"], default="sum",
                    help="chord score: total residual covered (sum) or per-pixel average (mean)")
    ap.add_argument("--gamma", type=float, default=1.0, help="gamma applied to the input (>1 darkens)")
    ap.add_argument("--no-autocontrast", action="store_true")
    ap.add_argument("--start", type=int, default=0, help="starting nail")
    ap.add_argument("--hoop-diameter", type=float, default=0.625, help="physical hoop diameter in metres")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    ap.add_argument("--name", default=None, help="basename for the outputs")
    ap.add_argument("--preview-size", type=int, default=1000)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    name = args.name or os.path.splitext(os.path.basename(args.image))[0]
    os.makedirs(args.out_dir, exist_ok=True)
    cache_dir = None if args.no_cache else os.path.join(args.out_dir, ".cache")
    verbose = not args.quiet

    t0 = time.time()
    residual = load_image(args.image, args.size, args.gamma, not args.no_autocontrast)
    if verbose:
        print(f"building chord table for {args.nails} nails at {args.size}px ...", file=sys.stderr)
    idx, seg, lengths = build_chord_table(args.nails, args.size, cache_dir)
    if verbose:
        print(f"  ready in {time.time() - t0:.1f}s; solving ...", file=sys.stderr)

    seq, _ = solve(residual, args.nails, args.lines, args.min_distance, args.min_loop,
                   args.line_weight, args.score, args.start, idx, seg, lengths, verbose)

    length_m = thread_length_m(seq, lengths, args.size, args.hoop_diameter)
    out = {
        "source": os.path.basename(args.image),
        "nails": args.nails,
        "nail_0": "12 o'clock, numbering clockwise when viewed from the front",
        "hoop_diameter_m": args.hoop_diameter,
        "lines": len(seq) - 1,
        "thread_length_m": round(length_m, 1),
        "params": {
            "min_distance": args.min_distance, "min_loop": args.min_loop,
            "line_weight": args.line_weight, "size": args.size, "score": args.score,
            "gamma": args.gamma, "autocontrast": not args.no_autocontrast,
        },
        "sequence": seq,
    }
    base = os.path.join(args.out_dir, name)
    with open(base + ".json", "w") as f:
        json.dump(out, f)
    with open(base + ".txt", "w") as f:
        f.write("\n".join(str(s) for s in seq) + "\n")
    render_fast(seq, args.nails, args.preview_size).save(base + ".png")

    if verbose:
        print(f"done: {len(seq) - 1} lines, {length_m:.0f} m of thread, {time.time() - t0:.1f}s total",
              file=sys.stderr)
        print(f"  {base}.json  {base}.txt  {base}.png", file=sys.stderr)


if __name__ == "__main__":
    main()
