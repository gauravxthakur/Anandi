"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, RotateCcw, Upload } from "lucide-react";
import { toast } from "sonner";

import {
  BiometryOverlay,
  OverlayHud,
} from "@/components/biometry/BiometryOverlay";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  BiometryApiError,
  isBiometryApiConfigured,
  predictHeadCircumference,
} from "@/lib/api/biometry";
import type { BiometryOverlayResult } from "@/lib/biometry-types";
import {
  buildDemoOverlay,
  hasOverlayGeometry,
  mapBackendEllipseToImage,
  overlaySlice,
} from "@/lib/overlay-geometry";
import { persistPredictionForForm, readPredictionForForm } from "@/lib/biometry-session";
type AnalyzeStatus = "idle" | "loading" | "success" | "error";

export function ScanInterface() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewUrlRef = useRef<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [overlay, setOverlay] = useState<BiometryOverlayResult | null>(null);
  const [status, setStatus] = useState<AnalyzeStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [clinicalGaWeeks, setClinicalGaWeeks] = useState<number | null>(null);
  const router = useRouter();

  const revokePreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => revokePreview();
  }, [revokePreview]);

  const resetAnalysis = useCallback(() => {
    setOverlay(null);
    setStatus("idle");
    setErrorMessage(null);
  }, []);

  const handleSubmitClinicalGa = () => {
    if (clinicalGaWeeks == null) {
      toast.error("Enter clinical GA before submitting.");
      return;
    }

    const snapshot = readPredictionForForm();
    persistPredictionForForm({
      hc_mm: snapshot?.hc_mm ?? null,
      ga_weeks_from_hc: snapshot?.ga_weeks_from_hc ?? null,
      growth_verdict: snapshot?.growth_verdict ?? null,
      hc_pixels: snapshot?.hc_pixels ?? null,
      clinical_ga_weeks: clinicalGaWeeks,
    });

    router.push("/patient-intake");
  };

  const handleFileChange = (next: File | null) => {
    revokePreview();
    resetAnalysis();
    setFile(next);
    setImageSize(null);

    if (!next) {
      setPreviewUrl(null);
      return;
    }

    const url = URL.createObjectURL(next);
    previewUrlRef.current = url;
    setPreviewUrl(url);
  };

  const runAnalysis = useCallback(async () => {
    if (!file) {
      toast.error("Choose an ultrasound image first.");
      return;
    }

    setStatus("loading");
    setErrorMessage(null);
    setOverlay(null);

    try {
      if (!isBiometryApiConfigured()) {
        await new Promise((r) => setTimeout(r, 600));
        if (!imageSize) {
          throw new Error("Wait for the image preview to load, then analyze again.");
        }
        const demoOverlay = buildDemoOverlay(
          imageSize.width,
          imageSize.height,
        );
        setOverlay(demoOverlay);
        persistPredictionForForm({
          hc_mm: null,
          ga_weeks_from_hc: 28.4,
          growth_verdict:
            "Demo overlay — correlate HC-derived GA with clinical dating before reporting.",
          hc_pixels: demoOverlay.hc_pixels,
        });
        toast.message("Demo overlay", {
          description:
            "Set NEXT_PUBLIC_BIOMETRY_API_URL and start the Python API for live inference.",
        });
      } else {
        const prediction = await predictHeadCircumference(file, clinicalGaWeeks);
        persistPredictionForForm({
          hc_mm: prediction.hc_mm ?? null,
          ga_weeks_from_hc: prediction.ga_weeks_from_hc ?? null,
          growth_verdict: prediction.growth_verdict ?? null,
          hc_pixels: prediction.hc_pixels ?? null,
          clinical_ga_weeks: clinicalGaWeeks ?? null,
        });
        setOverlay(overlaySlice(prediction));
        if (!hasOverlayGeometry(overlaySlice(prediction))) {
          toast.warning("Analysis finished", {
            description: "Model could not fit a valid ellipse on this frame.",
          });
        } else {
          toast.success("Head circumference detected");
        }
      }
      setStatus("success");
    } catch (err) {
      const message =
        err instanceof BiometryApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Analysis failed";
      setErrorMessage(message);
      setStatus("error");
      toast.error("Could not analyze image", { description: message });
    }
  }, [file, imageSize, clinicalGaWeeks]);

  useEffect(() => {
    if (!file || !previewUrl || status !== "idle" || overlay) return;
    if (!imageSize) return;
    void runAnalysis();
  }, [file, previewUrl, imageSize, status, overlay, runAnalysis]);

  const ellipse =
    overlay && imageSize
      ? mapBackendEllipseToImage(overlay, imageSize.width, imageSize.height)
      : null;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Ultrasound scan</h1>
          <p className="text-muted-foreground text-sm">
            Upload a fetal head frame — the model outlines the skull and reports HC in
            pixels.
          </p>
        </div>
        <nav className="shrink-0 text-sm font-medium">
          <Link
            href="/patient-intake"
            className="text-emerald-700 underline-offset-4 hover:underline dark:text-emerald-400"
          >
            Form F intake
          </Link>
        </nav>
      </header>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="ultrasound-file">Ultrasound image</Label>
          <Input
            id="ultrasound-file"
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="cursor-pointer"
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
          />
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="clinical-ga-weeks">Clinical Gestational Age (Weeks)</Label>
          <Input
            id="clinical-ga-weeks"
            type="number"
            placeholder="e.g., 28.5"
            value={clinicalGaWeeks ?? ""}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setClinicalGaWeeks(isNaN(val) ? null : val);
            }}
          />
          <Button
            type="button"
            variant="outline"
            disabled={clinicalGaWeeks == null}
            onClick={handleSubmitClinicalGa}
          >
            Submit GA
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            disabled={!file || status === "loading"}
            onClick={() => void runAnalysis()}
          >
            {status === "loading" ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                <Upload className="size-4" />
                Re-analyze
              </>
            )}
          </Button>
          {status === "error" ? (
            <Button
              type="button"
              variant="outline"
              disabled={!file}
              onClick={() => void runAnalysis()}
            >
              <RotateCcw className="size-4" />
              Retry
            </Button>
        ) : null}
      </div>
    </div>

      <div className="relative overflow-hidden rounded-xl border bg-zinc-950 shadow-lg ring-1 ring-emerald-500/20">
        {!previewUrl ? (
          <div className="flex aspect-[4/3] items-center justify-center text-sm text-zinc-400">
            Select an image to preview
          </div>
        ) : (
          <div className="relative aspect-[4/3] w-full bg-black">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="Uploaded ultrasound"
              className="h-full w-full object-contain"
              onLoad={(e) => {
                const img = e.currentTarget;
                setImageSize({
                  width: img.naturalWidth,
                  height: img.naturalHeight,
                });
              }}
            />
            {imageSize && overlay ? (
              <BiometryOverlay
                width={imageSize.width}
                height={imageSize.height}
                ellipse={ellipse}
                overlay={overlay}
              />
            ) : null}
            {status === "loading" ? (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-[1px]">
                <div className="flex items-center gap-2 rounded-lg bg-zinc-900/90 px-4 py-2 text-sm text-emerald-100">
                  <Loader2 className="size-4 animate-spin text-emerald-400" />
                  Running head circumference model…
                </div>
              </div>
            ) : null}
          </div>
        )}
        {overlay ? (
          <div className="border-t border-zinc-800 bg-zinc-950/95 px-3 py-2">
            <OverlayHud overlay={overlay} />
          </div>
        ) : null}
      </div>

      {errorMessage ? (
        <p className="text-destructive text-sm" role="alert">
          {errorMessage}
        </p>
      ) : null}

      {!isBiometryApiConfigured() ? (
        <p className="text-muted-foreground text-xs">
          Demo mode: no API URL configured. Start{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-[11px]">
            py -m uvicorn backend.api.main:app --port 8000
          </code>{" "}
          and set{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-[11px]">
            NEXT_PUBLIC_BIOMETRY_API_URL=http://localhost:8000
          </code>
          .
        </p>
      ) : null}
    </div>
  );
}

