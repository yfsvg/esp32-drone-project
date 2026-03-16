import cv2
import numpy as np
import argparse
import sys
import time
import threading
import torch
from ultralytics import YOLO

parser = argparse.ArgumentParser(description="Optimized ESP32 Grass Streamer - Threaded Frame Grab")
parser.add_argument("--source", default="0", help="Stream URL or 0 for webcam")
parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold")
parser.add_argument("--imgsz", type=int, default=320, help="Inference size")
parser.add_argument("--model", default="best.pt", help="Path to your trained YOLOv8 model")
parser.add_argument("--grid_res", type=int, default=100, help="Resolution of the processing grid (e.g., 100 for 100x100)")
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Threaded Frame Grabber — decouples camera I/O from inference loop
# ---------------------------------------------------------------------------
class FrameGrabber:
    """
    Runs cap.read() in a background thread so the main loop never blocks
    waiting on the camera. Eliminates the ~80ms frame_grab bottleneck.
    """
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # minimal OS buffer
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.frame  = None
        self.ret    = False
        self.lock   = threading.Lock()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret   = ret
                self.frame = frame

    def get(self):
        """Return (ret, frame) — always the freshest available frame."""
        with self.lock:
            return self.ret, (self.frame.copy() if self.frame is not None else None)

    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        self._thread.join(timeout=2)
        self.cap.release()

# ---------------------------------------------------------------------------
# Reference Images + Safety Checks
# ---------------------------------------------------------------------------
GOODGRASS    = cv2.imread('GRASSIMAGESAMPLES/MIgood.png')
ALRIGHTGRASS = cv2.imread('GRASSIMAGESAMPLES/MImedium.png')
BADGRASS     = cv2.imread('GRASSIMAGESAMPLES/MIbad.png')

if GOODGRASS is None or ALRIGHTGRASS is None or BADGRASS is None:
    print("[ERROR] Image upload error. Check GRASSIMAGESAMPLES/ paths.")
    sys.exit(1)


def get_iqr_hsv(image, mask=None):
    hsv    = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    pixels = hsv[mask].astype(np.float32) if mask is not None else hsv.reshape(-1, 3).astype(np.float32)
    result = []
    for i in range(3):
        ch = pixels[:, i]
        if len(ch) == 0:
            result.append(0.0)
            continue
        q25, q75 = np.percentile(ch, [25, 75])
        clipped  = ch[(ch >= q25) & (ch <= q75)]
        result.append(float(np.mean(clipped)) if len(clipped) > 0 else float(np.mean(ch)))
    return tuple(result)

healthy_median = np.array(get_iqr_hsv(GOODGRASS),    dtype=np.float32)
medium_median  = np.array(get_iqr_hsv(ALRIGHTGRASS), dtype=np.float32)
poor_median    = np.array(get_iqr_hsv(BADGRASS),      dtype=np.float32)

print(f"[INFO] Reference HSV — Good: {healthy_median} | Medium: {medium_median} | Poor: {poor_median}")

# ---------------------------------------------------------------------------
# Grass Quality Classification Params
# ---------------------------------------------------------------------------
HUE_GATE  = 15.0
DIST_GATE = 60.0

HUE_W, SAT_W, VAL_W = 3.0, 1.2, 0.5
WEIGHTS = np.array([HUE_W, SAT_W, VAL_W], dtype=np.float32)

COLORS = np.array([
    [0, 200, 0],    # Green  — Good
    [0, 200, 255],  # Yellow — Medium
    [0, 0, 220]     # Red    — Poor
], dtype=np.uint8)

# ---------------------------------------------------------------------------
# Device & Model
# ---------------------------------------------------------------------------
if torch.cuda.is_available():        DEVICE = "cuda"
elif torch.backends.mps.is_available(): DEVICE = "mps"
else:                                 DEVICE = "cpu"

print(f"[INFO] Loading {args.model} on {DEVICE}...")
try:
    model = YOLO(args.model)
    model(np.zeros((320, 320, 3), dtype=np.float32), device=DEVICE, verbose=False)
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Stream Setup — now using threaded grabber
# ---------------------------------------------------------------------------
def resolve_source(src):
    try: return int(src)
    except ValueError: return src

grabber = FrameGrabber(resolve_source(args.source))

if not grabber.isOpened():
    print(f"[ERROR] Cannot open video source: {args.source}")
    sys.exit(1)

# Give the grabber thread a moment to fill its first frame
time.sleep(0.5)

# ---------------------------------------------------------------------------
# Latency Profiler
# ---------------------------------------------------------------------------
PROFILE_INTERVAL = 60  # print summary every N frames

_timings = {
    "1_frame_grab":   [],
    "2_yolo":         [],
    "3_mask_process": [],
    "4_hsv_classify": [],
    "5_blend":        [],
    "6_total":        [],
}
_frame_count = 0

def _ms(t0, t1):
    return (t1 - t0) * 1000.0

def _print_latency_summary(timings, frame_count):
    print(f"\n{'='*65}")
    print(f"  LATENCY REPORT  (frames sampled: {frame_count})")
    print(f"{'='*65}")
    print(f"  {'Stage':<22} {'Mean':>8} {'P50':>8} {'P95':>8} {'P99':>8}")
    print(f"  {'-'*54}")
    for stage, vals in timings.items():
        if not vals:
            continue
        a     = np.array(vals)
        label = stage[2:]
        print(f"  {label:<22} {a.mean():>7.2f}ms {np.percentile(a,50):>7.2f}ms "
              f"{np.percentile(a,95):>7.2f}ms {np.percentile(a,99):>7.2f}ms")
    total_vals = timings.get("6_total")
    if total_vals:
        fps_arr = 1000.0 / np.array(total_vals)
        print(f"  {'-'*54}")
        print(f"  {'Throughput':<22} {fps_arr.mean():>7.1f} fps  "
              f"(p95 worst: {1000.0/np.percentile(total_vals,95):.1f} fps)")
    print(f"{'='*65}\n")

# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
print("[INFO] Starting stream. Press 'q' to quit.")
print(f"[INFO] Latency summary printed every {PROFILE_INTERVAL} frames.\n")

GRID_RES  = (args.grid_res, args.grid_res)
alpha     = 0.5
prev_time = 0

while True:
    t_loop_start = time.perf_counter()

    # ── Stage 1: Frame Grab (non-blocking — thread already decoded it) ───────
    t0 = time.perf_counter()
    ret, frame = grabber.get()
    t1 = time.perf_counter()
    _timings["1_frame_grab"].append(_ms(t0, t1))

    if not ret or frame is None:
        print("[WARN] No frame available yet, waiting...")
        time.sleep(0.05)
        continue

    h_frame, w_frame = frame.shape[:2]

    # ── Stage 2: YOLO Inference ──────────────────────────────────────────────
    t0 = time.perf_counter()
    results = model(frame, device=DEVICE, retina_masks=False,
                    imgsz=args.imgsz, conf=args.conf, verbose=False)
    t1 = time.perf_counter()
    _timings["2_yolo"].append(_ms(t0, t1))

    full_overlay    = np.zeros_like(frame)
    cells_processed = 0

    if results[0].masks is not None:
        # ── Stage 3: Mask Combine + Downsample + Blur ────────────────────────
        t0 = time.perf_counter()
        masks_tensor  = results[0].masks.data
        combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy().astype(np.uint8)

        small_frame   = cv2.resize(frame, GRID_RES, interpolation=cv2.INTER_LINEAR)
        small_mask    = cv2.resize(combined_mask, GRID_RES, interpolation=cv2.INTER_NEAREST).astype(bool)
        blurred_small = cv2.GaussianBlur(small_frame, (5, 5), 0)
        t1 = time.perf_counter()
        _timings["3_mask_process"].append(_ms(t0, t1))

        # ── Stage 4: HSV Conversion + Vectorized Classification ──────────────
        t0 = time.perf_counter()
        hsv_small = cv2.cvtColor(blurred_small, cv2.COLOR_BGR2HSV).astype(np.float32)

        hue_diffs      = np.abs(hsv_small[..., 0:1] - np.array([healthy_median[0], medium_median[0], poor_median[0]]))
        min_hue_dist   = np.min(hue_diffs, axis=-1)
        valid_hue_mask = min_hue_dist <= HUE_GATE

        def calc_dist(ref_hsv):
            diff = (hsv_small - ref_hsv) * WEIGHTS
            return np.sqrt(np.sum(diff**2, axis=-1))

        dists = np.stack([
            calc_dist(healthy_median),
            calc_dist(medium_median),
            calc_dist(poor_median)
        ], axis=-1)

        best_label_idx  = np.argmin(dists, axis=-1)
        min_dist_vals   = np.min(dists, axis=-1)
        valid_dist_mask = min_dist_vals <= DIST_GATE

        final_valid_mask = small_mask & valid_hue_mask & valid_dist_mask

        small_overlay = np.zeros_like(small_frame)
        small_overlay[final_valid_mask] = COLORS[best_label_idx[final_valid_mask]]
        cells_processed = np.count_nonzero(final_valid_mask)

        full_overlay = cv2.resize(small_overlay, (w_frame, h_frame), interpolation=cv2.INTER_NEAREST)
        t1 = time.perf_counter()
        _timings["4_hsv_classify"].append(_ms(t0, t1))

    # ── Stage 5: Alpha Blend + HUD ───────────────────────────────────────────
    t0 = time.perf_counter()
    active_overlay  = np.any(full_overlay != 0, axis=-1)
    annotated_frame = frame.copy()

    if np.any(active_overlay):
        blended = cv2.addWeighted(full_overlay, alpha, frame, 1 - alpha, 0)
        annotated_frame[active_overlay] = blended[active_overlay]
    t1 = time.perf_counter()
    _timings["5_blend"].append(_ms(t0, t1))

    # ── Total loop time ──────────────────────────────────────────────────────
    _timings["6_total"].append(_ms(t_loop_start, time.perf_counter()))

    # ── FPS counter ──────────────────────────────────────────────────────────
    curr_time = time.time()
    fps       = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
    prev_time = curr_time

    # ── Periodic latency summary ─────────────────────────────────────────────
    _frame_count += 1
    if _frame_count % PROFILE_INTERVAL == 0:
        _print_latency_summary(_timings, _frame_count)
        # Uncomment for rolling window instead of all-time averages:
        # for k in _timings: _timings[k].clear()

    # ── On-screen HUD ────────────────────────────────────────────────────────
    yolo_ms  = _timings["2_yolo"][-1]
    total_ms = _timings["6_total"][-1]
    cv2.putText(
        annotated_frame,
        f"FPS: {fps:.1f} | {GRID_RES[0]}x{GRID_RES[1]} | Areas: {cells_processed} "
        f"| YOLO: {yolo_ms:.1f}ms | Total: {total_ms:.1f}ms",
        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
    )

    cv2.imshow("Grass AI Streamer", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Final summary on exit
print("\n[INFO] Final latency summary:")
_print_latency_summary(_timings, _frame_count)

grabber.release()
cv2.destroyAllWindows()