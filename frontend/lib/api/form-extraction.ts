import type { FormFTrackedKey } from "@/lib/form-f-workflow";

const API_BASE = process.env.NEXT_PUBLIC_BIOMETRY_API_URL?.replace(/\/$/, "") ?? "";

export type FormExtractionFieldPayload = {
  aiSuggestion?: string;
  value?: string;
  citation?: string | null;
};

export type FormExtractionResponse = {
  fields: Partial<Record<FormFTrackedKey, FormExtractionFieldPayload>>;
  /** Optional global citation when OCR layer supplies references */
  citation?: string | null;
};

/**
 * Optional OCR / NLP extraction for Form F. When the backend omits this route,
 * the UI relies on scan session bridge (`biometry-session`) instead.
 */
export async function fetchFormExtraction(): Promise<FormExtractionResponse | null> {
  if (!API_BASE) return null;
  try {
    const res = await fetch(`${API_BASE}/extract/form-f`, { method: "POST" });
    if (!res.ok) return null;
    return (await res.json()) as FormExtractionResponse;
  } catch {
    return null;
  }
}
