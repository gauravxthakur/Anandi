/** Strike B — minimal per-field workflow (approve / edit). */

export type FormFTrackedKey =
  | "gestationalAgeWeeks"
  | "headCircumferenceMm"
  | "resultOfProcedure";

export type TrackedFieldState = {
  aiSuggestion: string;
  value: string;
  approved: boolean;
};

export const INITIAL_TRACKED_FIELDS: Record<FormFTrackedKey, TrackedFieldState> = {
  gestationalAgeWeeks: { aiSuggestion: "", value: "", approved: false },
  headCircumferenceMm: { aiSuggestion: "", value: "", approved: false },
  resultOfProcedure: { aiSuggestion: "", value: "", approved: false },
};

export function allTrackedApproved(
  fields: Record<FormFTrackedKey, TrackedFieldState>,
): boolean {
  return (
    fields.gestationalAgeWeeks.approved &&
    fields.headCircumferenceMm.approved &&
    fields.resultOfProcedure.approved
  );
}

/** Single citation line when API text is unavailable (Hadlock norms — demo fallback only). */
export const HADLOCK_GA_FALLBACK_CITATION =
  "Hadlock FP et al., Radiology (1984): fetal head circumference vs gestational age reference — HC-derived GA must be correlated with clinical dating.";
