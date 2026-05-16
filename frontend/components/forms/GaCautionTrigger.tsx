"use client";

import { AlertTriangle } from "lucide-react";

import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { HADLOCK_GA_FALLBACK_CITATION } from "@/lib/form-f-workflow";

export type GaCautionTriggerProps = {
  /** Show caution affordance when clinical vs HC-derived GA differs by more than 1 week */
  active: boolean;
  reasoning: string;
  /** Prefer backend text (e.g. growth_verdict or OCR citation); fallback is Hadlock line only */
  citation: string | null;
};

export function GaCautionTrigger({
  active,
  reasoning,
  citation,
}: GaCautionTriggerProps) {
  if (!active) return null;

  const cite =
    citation?.trim() && citation.trim().length > 0
      ? citation.trim()
      : HADLOCK_GA_FALLBACK_CITATION;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="size-7 text-amber-600 hover:bg-amber-500/15 hover:text-amber-700 dark:text-amber-400 dark:hover:text-amber-300"
          aria-label="Gestational age discrepancy — details"
        >
          <AlertTriangle className="size-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-80 space-y-2">
        <PopoverHeader>
          <PopoverTitle className="text-amber-900 dark:text-amber-100">
            GA mismatch caution
          </PopoverTitle>
          <PopoverDescription className="text-foreground">
            {reasoning}
          </PopoverDescription>
        </PopoverHeader>
        <p className="text-muted-foreground border-t pt-2 text-xs leading-relaxed">
          <span className="font-medium text-foreground">Citation: </span>
          {cite}
        </p>
      </PopoverContent>
    </Popover>
  );
}
