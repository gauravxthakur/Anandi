import { z } from "zod";

export const patientIntakeSchema = z
  .object({
    fullName: z.string().min(1, "Full name is required"),
    age: z.coerce.number().int().min(10).max(60),
    husbandOrFatherName: z.string().min(1, "This field is required"),
    contactNumber: z.string().min(7, "Contact number is too short"),
    postalAddress: z.string().min(1, "Address is required"),

    livingChildrenTotal: z.coerce.number().int().min(0),
    livingSonsCount: z.coerce.number().int().min(0),
    livingSonsAges: z.string().optional().default(""),
    livingDaughtersCount: z.coerce.number().int().min(0),
    livingDaughtersAges: z.string().optional().default(""),
    lmpOrWeeks: z.string().min(1, "LMP / Weeks is required"),

    referralSource: z.enum(["self", "external"]),
    referringDoctorNameAddress: z.string().optional().default(""),

    indicationForUltrasound: z.array(z.string()).default([]),
    resultOfProcedure: z.string().optional().default(""),
    indicationForMtp: z.boolean().default(false),

    dateOfProcedure: z.string().min(1),
    patientConsentNoSexDisclosure: z.boolean().default(false),
    doctorConfirmationNoSexDisclosure: z.boolean().default(false),
  })
  .superRefine((data, ctx) => {
    if (
      data.referralSource === "external" &&
      !data.referringDoctorNameAddress?.trim()
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["referringDoctorNameAddress"],
        message: "Referring doctor name/address is required for external referral",
      });
    }
  });

// Useful types:
// - `PatientIntakeFormValues`: raw form values (what react-hook-form deals with)
// - `PatientIntakeParsedValues`: parsed/validated values (output after Zod coercion)
export type PatientIntakeFormValues = z.input<typeof patientIntakeSchema>;
export type PatientIntakeParsedValues = z.output<typeof patientIntakeSchema>;
