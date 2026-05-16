"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { downloadBlob, generateReport } from "@/lib/api/report";
import type { PatientIntakeParsedValues } from "@/lib/patient-intake-schema";
import type { BiometryPrediction } from "@/lib/biometry-types";

interface ReportPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient: PatientIntakeParsedValues | null;
  biometry?: BiometryPrediction | null;
}

export function ReportPreviewModal({
  open,
  onOpenChange,
  patient,
  biometry,
}: ReportPreviewModalProps) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGeneratePdf = async () => {
    if (!patient) {
      toast.error("No patient data available");
      return;
    }

    setIsGenerating(true);
    try {
      const blob = await generateReport({ patient, biometry });

      // Format filename: patient name + date
      const sanitizedName = patient.fullName
        .toLowerCase()
        .replace(/\s+/g, "_")
        .replace(/[^a-z0-9_]/g, "");
      const today = new Date().toISOString().split("T")[0];
      const filename = `report_${sanitizedName}_${today}.pdf`;

      downloadBlob(blob, filename);
      toast.success("Report downloaded successfully");
      onOpenChange(false);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to generate report";
      toast.error(message);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!patient) return null;

  const indicationText =
    Array.isArray(patient.indicationForUltrasound) &&
    patient.indicationForUltrasound.length > 0
      ? patient.indicationForUltrasound.join(", ")
      : "Not specified";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Report Preview</DialogTitle>
          <DialogDescription>
            Review the patient information and biometry results before generating
            the official PDF report.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Patient Information */}
          <Card className="border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950">
            <h3 className="font-semibold text-emerald-900 dark:text-emerald-100">
              Patient Information
            </h3>
            <div className="mt-3 space-y-2 text-sm">
              <p>
                <span className="font-medium">Name:</span> {patient.fullName}
              </p>
              <p>
                <span className="font-medium">Age:</span> {patient.age} years
              </p>
              <p>
                <span className="font-medium">Contact:</span>{" "}
                {patient.contactNumber || "Not provided"}
              </p>
              <p>
                <span className="font-medium">LMP/Weeks:</span>{" "}
                {patient.lmpOrWeeks || "Not specified"}
              </p>
              <p>
                <span className="font-medium">Date of Procedure:</span>{" "}
                {new Date(patient.dateOfProcedure).toLocaleDateString()}
              </p>
            </div>
          </Card>

          {/* Obstetric History */}
          <Card className="border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
            <h3 className="font-semibold text-blue-900 dark:text-blue-100">
              Obstetric History
            </h3>
            <div className="mt-3 space-y-2 text-sm">
              <p>
                <span className="font-medium">Living Children:</span>{" "}
                {patient.livingChildrenTotal}
              </p>
              <p>
                <span className="font-medium">Living Sons:</span>{" "}
                {patient.livingSonsCount}{patient.livingSonsAges && ` (${patient.livingSonsAges})`}
              </p>
              <p>
                <span className="font-medium">Living Daughters:</span>{" "}
                {patient.livingDaughtersCount}
                {patient.livingDaughtersAges &&
                  ` (${patient.livingDaughtersAges})`}
              </p>
            </div>
          </Card>

          {/* Biometry Results */}
          {biometry && (
            <Card className="border-purple-200 bg-purple-50 p-4 dark:border-purple-900 dark:bg-purple-950">
              <h3 className="font-semibold text-purple-900 dark:text-purple-100">
                Fetal Head Circumference
              </h3>
              <div className="mt-3 space-y-2 text-sm">
                <p>
                  <span className="font-medium">HC:</span>{" "}
                  {biometry.hc_mm ? `${biometry.hc_mm.toFixed(1)} mm` : "Not measured"}
                </p>
                {biometry.ga_weeks_from_hc && (
                  <p>
                    <span className="font-medium">GA from HC:</span>{" "}
                    {biometry.ga_weeks_from_hc.toFixed(1)} weeks
                  </p>
                )}
                {biometry.growth_verdict && (
                  <p>
                    <span className="font-medium">Growth Assessment:</span>{" "}
                    {biometry.growth_verdict}
                  </p>
                )}
              </div>
            </Card>
          )}

          {/* Clinical Findings */}
          <Card className="border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
            <h3 className="font-semibold text-amber-900 dark:text-amber-100">
              Clinical Findings
            </h3>
            <div className="mt-3 space-y-2 text-sm">
              <p>
                <span className="font-medium">Indication:</span> {indicationText}
              </p>
              <p>
                <span className="font-medium">Result:</span>{" "}
                {patient.resultOfProcedure || "No findings recorded"}
              </p>
            </div>
          </Card>

          {/* Sign-off */}
          <Card className="border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              Digital Sign-off
            </h3>
            <div className="mt-3 space-y-2 text-sm">
              <p>
                <span className="font-medium">Patient Consent (No Sex Disclosure):</span>{" "}
                {patient.patientConsentNoSexDisclosure ? "✓ Yes" : "✗ No"}
              </p>
              <p>
                <span className="font-medium">Doctor Confirmation:</span>{" "}
                {patient.doctorConfirmationNoSexDisclosure ? "✓ Yes" : "✗ No"}
              </p>
            </div>
          </Card>

          {/* Disclaimer */}
          <Card className="border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950">
            <p className="text-xs text-red-700 dark:text-red-200">
              <span className="font-semibold">Disclaimer:</span> This report is a clinical
              summary generated with AI assistance. The clinician has reviewed and
              verified all measurements and findings before sign-off. This report is
              intended for clinical reference only.
            </p>
          </Card>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleGeneratePdf}
            disabled={isGenerating}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Generate & Download PDF
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
