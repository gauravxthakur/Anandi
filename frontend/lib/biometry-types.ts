/** Coarse quality tier from backend ``quality_flag``. */
export type QualityFlag = "HIGH" | "MEDIUM" | "LOW";

/**
 * Fields required for Strike A (SVG overlay). Matches ``single_predict`` geometry +
 * confidence / quality.
 */
export type BiometryOverlayResult = {
  hc_pixels: number | null;
  center: [number, number] | null;
  axes: [number, number] | null;
  angle: number | null;
  confidence: number | null;
  quality_flag: QualityFlag;
  quality_reasons?: string[];
};

/** Full prediction payload from ``POST /predict/hc``. */
export type BiometryPrediction = BiometryOverlayResult & {
  hc_mm?: number | null;
  calibration?: string;
  quality_reasons?: string[];
  ga_weeks_from_hc?: number | null;
  growth_code?: string;
  growth_verdict?: string | null;
  image_path?: string;
};
