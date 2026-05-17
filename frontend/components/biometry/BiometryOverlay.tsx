"use client";

import type { BiometryOverlayResult, QualityFlag } from "@/lib/biometry-types";
import type { MappedEllipse } from "@/lib/overlay-geometry";
import { cn } from "@/lib/utils";

const QUALITY_STYLES: Record<
  QualityFlag,
  { label: string; stroke: string; dash?: string }
> = {
  HIGH: {
    label: "High quality",
    stroke: "rgb(52, 211, 153)",
  },
  MEDIUM: {
    label: "Review suggested",
    stroke: "rgb(251, 191, 36)",
    dash: "6 4",
  },
  LOW: {
    label: "Low confidence",
    stroke: "rgb(248, 113, 113)",
    dash: "4 4",
  },
};

const DEFAULT_QUALITY_STYLE = {
  label: "Quality unavailable",
  stroke: "rgb(148, 163, 184)",
  dash: undefined,
};

export type BiometryOverlayProps = {
  width: number;
  height: number;
  ellipse: MappedEllipse | null;
  overlay: BiometryOverlayResult;
  className?: string;
};

export function BiometryOverlay({
  width,
  height,
  ellipse,
  overlay,
  className,
}: BiometryOverlayProps) {
  const quality = QUALITY_STYLES[overlay.quality_flag] ?? DEFAULT_QUALITY_STYLE;
  const showEllipse = ellipse != null;

  return (
    <svg
      className={cn("pointer-events-none absolute inset-0 h-full w-full", className)}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden
    >
      <defs>
        <filter id="hc-emerald-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow
            dx="0"
            dy="0"
            stdDeviation="4"
            floodColor="#34d399"
            floodOpacity="0.85"
          />
        </filter>
      </defs>

      {showEllipse ? (
        <>
          <ellipse
            cx={ellipse.cx}
            cy={ellipse.cy}
            rx={ellipse.rx}
            ry={ellipse.ry}
            transform={`rotate(${ellipse.rotationDeg} ${ellipse.cx} ${ellipse.cy})`}
            fill="none"
            stroke={quality.stroke}
            strokeWidth={2.5}
            strokeDasharray={quality.dash}
            filter="url(#hc-emerald-glow)"
          />
          {overlay.hc_pixels != null ? (
            <text
              x={ellipse.cx}
              y={Math.max(16, ellipse.cy - ellipse.ry - 10)}
              textAnchor="middle"
              className="fill-emerald-300 text-[11px] font-medium"
              style={{ fontSize: Math.max(11, width * 0.018) }}
            >
              HC {Math.round(overlay.hc_pixels)} px
            </text>
          ) : null}
        </>
      ) : (
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          className="fill-amber-200 text-sm"
        >
          No ellipse detected
        </text>
      )}
    </svg>
  );
}

export function OverlayHud({
  overlay,
  className,
}: {
  overlay: BiometryOverlayResult;
  className?: string;
}) {
  const quality = QUALITY_STYLES[overlay.quality_flag] ?? DEFAULT_QUALITY_STYLE;
  const confidencePct =
    overlay.confidence != null ? Math.round(overlay.confidence * 100) : null;
  const showWarning =
    overlay.quality_flag !== "HIGH" || overlay.confidence == null;

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <span className="rounded-md bg-emerald-950/80 px-2 py-0.5 text-xs font-medium text-emerald-100 ring-1 ring-emerald-500/40">
        {quality.label}
      </span>
      {confidencePct != null ? (
        <span className="rounded-md bg-black/55 px-2 py-0.5 text-xs text-white">
          Mask confidence {confidencePct}%
        </span>
      ) : (
        <span className="rounded-md bg-black/55 px-2 py-0.5 text-xs text-white">
          Confidence unavailable
        </span>
      )}
      {showWarning ? (
        <span className="rounded-md border border-amber-400/60 bg-amber-950/80 px-2 py-0.5 text-xs text-amber-100">
          Verify measurement before reporting
        </span>
      ) : null}
    </div>
  );
}
