/** Bridges HC inference results into Form F (session-only for demos). */

export const BIOMETRY_FORM_BRIDGE_KEY = "biometry:formBridge:v1";

export type FormBridgePrediction = {
  hc_mm: number | null;
  ga_weeks_from_hc: number | null;
  growth_verdict: string | null;
  hc_pixels: number | null;
  capturedAt: string;
};

export function persistPredictionForForm(
  data: Omit<FormBridgePrediction, "capturedAt">,
): void {
  if (typeof window === "undefined") return;
  const payload: FormBridgePrediction = {
    ...data,
    capturedAt: new Date().toISOString(),
  };
  sessionStorage.setItem(BIOMETRY_FORM_BRIDGE_KEY, JSON.stringify(payload));
}

export function readPredictionForForm(): FormBridgePrediction | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(BIOMETRY_FORM_BRIDGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as FormBridgePrediction;
    return parsed;
  } catch {
    return null;
  }
}
