import type { BiometryPrediction } from "@/lib/biometry-types";

const API_BASE = process.env.NEXT_PUBLIC_BIOMETRY_API_URL?.replace(/\/$/, "") ?? "";

export function isBiometryApiConfigured(): boolean {
  return API_BASE.length > 0;
}

export class BiometryApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "BiometryApiError";
    this.status = status;
  }
}

export async function predictHeadCircumference(
  file: File,
  clinicalGaWeeks?: number | null,
  options?: { pixelSpacingMm?: number },
): Promise<BiometryPrediction> {
  if (!isBiometryApiConfigured()) {
    throw new BiometryApiError(
      "Set NEXT_PUBLIC_BIOMETRY_API_URL to your inference server (e.g. http://localhost:8000).",
      0,
    );
  }

  const form = new FormData();
  form.append("file", file);

  const params = new URLSearchParams();
  if (options?.pixelSpacingMm != null) {
    params.set("pixel_spacing_mm", String(options.pixelSpacingMm));
  }
  if (clinicalGaWeeks != null) {
    params.set("clinical_ga_weeks", String(clinicalGaWeeks));
  }

  const qs = params.toString();
  const url = `${API_BASE}/predict/hc${qs ? `?${qs}` : ""}`;

  const response = await fetch(url, { method: "POST", body: form });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new BiometryApiError(detail || "Analysis failed", response.status);
  }

  return (await response.json()) as BiometryPrediction;
}

