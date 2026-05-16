import type { BiometryOverlayResult } from "@/lib/biometry-types";

/** Low-res model canvas (``768/4`` × ``512/4``). */
export const MODEL_WIDTH = 192;
export const MODEL_HEIGHT = 128;
export const UPSAMPLE_FACTOR = 16;

export type MappedEllipse = {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  rotationDeg: number;
};

export function hasOverlayGeometry(
  overlay: BiometryOverlayResult | null,
): overlay is BiometryOverlayResult & {
  center: [number, number];
  axes: [number, number];
  angle: number;
} {
  if (!overlay) return false;
  return (
    overlay.center != null &&
    overlay.axes != null &&
    overlay.angle != null &&
    overlay.hc_pixels != null
  );
}

/**
 * Map backend ellipse (row/col indexing on original image pixels) to SVG coords.
 *
 * Backend: origin top-left, x = row (down), y = column (right).
 * SVG: x = column, y = row.
 */
export function mapBackendEllipseToImage(
  overlay: BiometryOverlayResult,
  imageWidth: number,
  imageHeight: number,
): MappedEllipse | null {
  if (!hasOverlayGeometry(overlay)) return null;

  const [row, col] = overlay.center;
  const [a, b] = overlay.axes;
  const theta = overlay.angle;

  const cx = col;
  const cy = row;
  const rx = b;
  const ry = a;
  const rotationDeg = (theta * 180) / Math.PI;

  if (
    !Number.isFinite(cx) ||
    !Number.isFinite(cy) ||
    !Number.isFinite(rx) ||
    !Number.isFinite(ry) ||
    imageWidth <= 0 ||
    imageHeight <= 0
  ) {
    return null;
  }

  return { cx, cy, rx, ry, rotationDeg };
}

/** Demo ellipse when API URL is unset (UI-only). */
export function buildDemoOverlay(
  imageWidth: number,
  imageHeight: number,
): BiometryOverlayResult {
  const cx = imageWidth * 0.5;
  const cy = imageHeight * 0.42;
  const rx = imageWidth * 0.22;
  const ry = imageHeight * 0.16;
  const hc = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2);

  return {
    hc_pixels: Math.round(hc),
    center: [cy, cx],
    axes: [ry, rx],
    angle: 0,
    confidence: 0.82,
    quality_flag: "MEDIUM",
    quality_reasons: ["Demo overlay — connect backend for live inference"],
  };
}

export function overlaySlice(
  prediction: BiometryOverlayResult,
): BiometryOverlayResult {
  return {
    hc_pixels: prediction.hc_pixels,
    center: prediction.center,
    axes: prediction.axes,
    angle: prediction.angle,
    confidence: prediction.confidence,
    quality_flag: prediction.quality_flag,
    quality_reasons: prediction.quality_reasons,
  };
}
