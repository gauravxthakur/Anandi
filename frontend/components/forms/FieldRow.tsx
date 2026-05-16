"use client";

import { useEffect, useState } from "react";
import { Check, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export type FieldRowProps = {
  id: string;
  label: React.ReactNode;
  /** Rendered beside the label (e.g. caution trigger). */
  labelAccessory?: React.ReactNode;
  value: string;
  onChange: (next: string) => void;
  aiSuggestion?: string;
  approved: boolean;
  onApprovedChange: (approved: boolean) => void;
  multiline?: boolean;
  placeholder?: string;
  inputClassName?: string;
};

export function FieldRow({
  id,
  label,
  labelAccessory,
  value,
  onChange,
  aiSuggestion,
  approved,
  onApprovedChange,
  multiline,
  placeholder,
  inputClassName,
}: FieldRowProps) {
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (approved) setEditing(false);
  }, [approved]);

  const handleEdit = () => {
    onApprovedChange(false);
    setEditing(true);
    queueMicrotask(() => {
      document.getElementById(id)?.focus();
    });
  };

  const handleApprove = (checked: boolean) => {
    if (checked) setEditing(false);
    onApprovedChange(checked);
  };

  const locked = approved || !editing;

  const inputClass = cn(
    locked ? "cursor-default bg-muted/40 border-muted" : undefined,
    inputClassName,
  );

  return (
    <div className="space-y-2 rounded-lg border bg-card/50 p-3 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Label htmlFor={id} className="text-sm font-medium">
              {label}
            </Label>
            {labelAccessory}
          </div>
          {aiSuggestion ? (
            <p className="text-muted-foreground text-xs">
              AI suggestion:{" "}
              <span className="font-medium text-foreground">{aiSuggestion}</span>
            </p>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleEdit}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
          <div className="flex items-center gap-1.5 rounded-md border px-2 py-1">
            <Checkbox
              id={`${id}-approve`}
              checked={approved}
              onCheckedChange={(v) => handleApprove(Boolean(v))}
            />
            <Label
              htmlFor={`${id}-approve`}
              className="cursor-pointer text-xs font-normal"
            >
              Approve
            </Label>
          </div>
        </div>
      </div>

      {multiline ? (
        <Textarea
          id={id}
          rows={4}
          value={value}
          readOnly={locked}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className={inputClass}
        />
      ) : (
        <Input
          id={id}
          value={value}
          readOnly={locked}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className={inputClass}
        />
      )}

      {approved ? (
        <p className="flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-400">
          <Check className="size-3.5 shrink-0" />
          Verified for submission
        </p>
      ) : (
        <p className="text-muted-foreground text-xs">
          Use Edit to change this field, then Approve when it matches the chart.
        </p>
      )}
    </div>
  );
}
