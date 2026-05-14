import { z } from "zod";

// Regex for a comma-separated list of ages (e.g., "5, 8, 12")
const ageListRegex = /^(\d+(\s*,\s*\d+)*)?$/;

export const patientIntakeSchema = z
  .object({
    fullName: z
      .string()
      .trim()
      .min(1, "Full name is required")
      .max(100, "Full name is too long"),
    age: z.coerce
      .number()
      .int()
      .min(18, "Age must be at least 18")
      .max(60, "Age cannot exceed 60"),
    husbandOrFatherName: z
      .string()
      .trim()
      .min(1, "This field is required")
      .max(100, "Name is too long"),
    contactNumber: z
      .string()
      .trim()
      .regex(/^[6-9]\d{9}$/, "Invalid Indian contact number (10 digits starting with 6-9)"),
    postalAddress: z
      .string()
      .trim()
      .min(1, "Address is required")
      .max(500, "Address is too long"),

    livingChildrenTotal: z.coerce.number().int().min(0, "Cannot be negative"),
    livingSonsCount: z.coerce.number().int().min(0, "Cannot be negative"),
    livingSonsAges: z
      .string()
      .trim()
      .regex(ageListRegex, "Enter ages separated by commas (e.g. 5, 8)")
      .optional()
      .default(""),
    livingDaughtersCount: z.coerce.number().int().min(0, "Cannot be negative"),
    livingDaughtersAges: z
      .string()
      .trim()
      .regex(ageListRegex, "Enter ages separated by commas (e.g. 5, 8)")
      .optional()
      .default(""),

    lmpOrWeeks: z
      .string()
      .trim()
      .min(1, "LMP / Weeks is required")
      .refine(
        (val) => {
          // 1. Check if it's numeric weeks (e.g., "12", "12w", "12 weeks")
          const numericPart = val.replace(/\s*(weeks?|w)$/i, "");
          if (/^\d+$/.test(numericPart)) {
            const weeks = parseInt(numericPart, 10);
            return weeks >= 0 && weeks <= 45;
          }
          // 2. Check if it's a valid date (YYYY-MM-DD)
          if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
            const date = new Date(val);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            // Must be a valid date and not in the future
            return !isNaN(date.getTime()) && date <= today;
          }
          return false;
        },
        { message: "Enter weeks (0-45) or a valid past date (YYYY-MM-DD)" }
      ),

    referralSource: z.enum(["self", "external"]),
    referringDoctorNameAddress: z
      .string()
      .trim()
      .max(500, "Referral info is too long")
      .optional()
      .default(""),

    indicationForUltrasound: z
      .array(z.string())
      .min(1, "At least one indication for ultrasound must be selected")
      .default([]),
    resultOfProcedure: z
      .string()
      .trim()
      .max(1000, "Result text is too long")
      .optional()
      .default(""),
    indicationForMtp: z.boolean().default(false),

    dateOfProcedure: z
      .string()
      .min(1, "Date of procedure is required")
      .refine((str) => {
        const selectedDate = new Date(str);
        if (isNaN(selectedDate.getTime())) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return selectedDate <= today;
      }, "Date of procedure must be a valid date and cannot be in the future"),

    patientConsentNoSexDisclosure: z.boolean().refine((val) => val === true, "Patient consent is mandatory"),
    doctorConfirmationNoSexDisclosure: z.boolean().refine((val) => val === true, "Doctor's confirmation is mandatory"),
  })
  .superRefine((data, ctx) => {
    // 1. Conditional requirement for referral info
    if (data.referralSource === "external" && !data.referringDoctorNameAddress?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["referringDoctorNameAddress"],
        message: "Referring doctor name/address is required for external referral",
      });
    }

    // 2. Cross-field validation for children count
    if (data.livingSonsCount + data.livingDaughtersCount !== data.livingChildrenTotal) {
      const msg = `Sum of sons (${data.livingSonsCount}) and daughters (${data.livingDaughtersCount}) must equal total children (${data.livingChildrenTotal})`;
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["livingChildrenTotal"],
        message: msg,
      });
    }

    // 3. Conditional requirements for ages
    if (data.livingSonsCount > 0 && !data.livingSonsAges?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["livingSonsAges"],
        message: "Ages of living sons are required",
      });
    }
    if (data.livingDaughtersCount > 0 && !data.livingDaughtersAges?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["livingDaughtersAges"],
        message: "Ages of living daughters are required",
      });
    }
  });

export type PatientIntakeFormValues = z.input<typeof patientIntakeSchema>;
export type PatientIntakeParsedValues = z.output<typeof patientIntakeSchema>;






















































































































