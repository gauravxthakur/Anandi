import type { PatientIntakeParsedValues } from "@/lib/patient-intake-schema";
import type { BiometryPrediction } from "@/lib/biometry-types";

const API_BASE = process.env.NEXT_PUBLIC_BIOMETRY_API_URL?.replace(/\/$/, "") ?? "";

export class ReportApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ReportApiError";
    this.status = status;
  }
}

export interface ReportGenerateRequest {
  patient: PatientIntakeParsedValues;
  biometry?: BiometryPrediction | null;
}

/**
 * Generate a PDF report via the backend endpoint.
 * Returns a blob that can be downloaded as a PDF file.
 */
export async function generateReport(
  request: ReportGenerateRequest,
): Promise<Blob> {
  if (!API_BASE) {
    throw new ReportApiError(
      "Set NEXT_PUBLIC_BIOMETRY_API_URL to your inference server (e.g. http://localhost:8000).",
      0,
    );
  }

  const url = `${API_BASE}/report/generate`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ReportApiError(
      detail || "Report generation failed",
      response.status,
    );
  }

  const json = (await response.json()) as { pdf_base64?: string };
  
  if (!json.pdf_base64) {
    throw new ReportApiError("No PDF data in response", 500);
  }

  // Convert base64 to blob
  const binaryString = atob(json.pdf_base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  
  return new Blob([bytes], { type: "application/pdf" });
}

/**
 * Download a blob as a file in the browser.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
