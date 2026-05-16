/** Parse clinical gestational age (weeks) from Form F “LMP / weeks” field + procedure date. */

export function parseClinicalGaWeeks(
  lmpOrWeeks: string,
  procedureDateIso: string,
): number | null {
  const trimmed = lmpOrWeeks.trim();
  const numericPart = trimmed.replace(/\s*(weeks?|w)$/i, "");
  if (/^\d+$/.test(numericPart)) {
    const w = parseInt(numericPart, 10);
    if (w >= 0 && w <= 45) return w;
    return null;
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    const lmp = new Date(`${trimmed}T12:00:00`);
    const proc = new Date(`${procedureDateIso}T12:00:00`);
    if (Number.isNaN(lmp.getTime()) || Number.isNaN(proc.getTime())) return null;
    const msPerDay = 86_400_000;
    const days = Math.floor((proc.getTime() - lmp.getTime()) / msPerDay);
    if (days < 0 || days > 315) return null;
    return Math.round((days / 7) * 10) / 10;
  }

  return null;
}

export function parseWeeksFloat(raw: string): number | null {
  const n = parseFloat(raw.trim().replace(",", "."));
  if (!Number.isFinite(n)) return null;
  return n;
}
