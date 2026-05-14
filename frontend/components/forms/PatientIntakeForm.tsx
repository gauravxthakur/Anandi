"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { FormSectionCard } from "@/components/form-section-card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  RadioGroup,
  RadioGroupItem,
} from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group";
import { Textarea } from "@/components/ui/textarea";

import {
  patientIntakeSchema,
  type PatientIntakeFormValues,
  type PatientIntakeParsedValues,
} from "@/lib/patient-intake-schema";

function getTodayIsoDate() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-sm text-destructive">{message}</p>;
}

export function PatientIntakeForm() {
  const form = useForm<PatientIntakeFormValues>({
    resolver: zodResolver(patientIntakeSchema),
    defaultValues: {
      fullName: "",
      age: 25,
      husbandOrFatherName: "",
      contactNumber: "",
      postalAddress: "",

      livingChildrenTotal: 0,
      livingSonsCount: 0,
      livingSonsAges: "",
      livingDaughtersCount: 0,
      livingDaughtersAges: "",
      lmpOrWeeks: "",

      referralSource: "self",
      referringDoctorNameAddress: "",

      indicationForUltrasound: [],
      resultOfProcedure: "",
      indicationForMtp: false,

      dateOfProcedure: getTodayIsoDate(),
      patientConsentNoSexDisclosure: false,
      doctorConfirmationNoSexDisclosure: false,
    },
    mode: "onBlur",
  });

  const referralSource = form.watch("referralSource");
  const selectedIndications = form.watch("indicationForUltrasound");

  const onSubmit = (values: PatientIntakeFormValues) => {
    const parsed: PatientIntakeParsedValues = patientIntakeSchema.parse(values);
    // For now: just log + toast. You can later POST this to your API.
    console.log("PatientIntake:", parsed);
    toast.success("Form saved");
  };

  return (
    <div className="flex flex-1 justify-center bg-muted/30 px-4 py-10">
      <div className="w-full max-w-4xl">
        <div className="mb-8 space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Patient Intake
          </h1>
          <p className="text-sm text-muted-foreground">
            Fill patient identity, obstetric history, referral details, AI insights,
            and declarations.
          </p>
        </div>

        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="space-y-6"
        >
          <FormSectionCard
            title="Card 1: Patient Identity"
            description="Legal name, age, next of kin, contact, and mailing address for this visit."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input id="fullName" {...form.register("fullName")} />
                <FieldError message={form.formState.errors.fullName?.message} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="age">Age</Label>
                <Input id="age" type="number" {...form.register("age")} />
                <FieldError message={form.formState.errors.age?.message} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="husbandOrFatherName">Husband’s / Father’s Name</Label>
                <Input
                  id="husbandOrFatherName"
                  {...form.register("husbandOrFatherName")}
                />
                <FieldError
                  message={form.formState.errors.husbandOrFatherName?.message}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contactNumber">Contact Number</Label>
                <Input id="contactNumber" {...form.register("contactNumber")} />
                <FieldError
                  message={form.formState.errors.contactNumber?.message}
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="postalAddress">Full Postal Address</Label>
                <Textarea
                  id="postalAddress"
                  rows={3}
                  {...form.register("postalAddress")}
                />
                <FieldError
                  message={form.formState.errors.postalAddress?.message}
                />
              </div>
            </div>
          </FormSectionCard>

          <FormSectionCard
            title="Card 2: Obstetric History"
            description="Living children, LMP or current gestation, and ages where applicable."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="livingChildrenTotal">
                  Total Number of Living Children
                </Label>
                <Input
                  id="livingChildrenTotal"
                  type="number"
                  {...form.register("livingChildrenTotal")}
                />
                <FieldError
                  message={form.formState.errors.livingChildrenTotal?.message}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="lmpOrWeeks">LMP or Current Weeks of Pregnancy</Label>
                <Input id="lmpOrWeeks" {...form.register("lmpOrWeeks")} />
                <FieldError message={form.formState.errors.lmpOrWeeks?.message} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="livingSonsCount">Number of Living Sons</Label>
                <Input
                  id="livingSonsCount"
                  type="number"
                  {...form.register("livingSonsCount")}
                />
                <FieldError message={form.formState.errors.livingSonsCount?.message} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="livingSonsAges">Living Sons (ages)</Label>
                <Input
                  id="livingSonsAges"
                  placeholder="e.g. 7, 3"
                  {...form.register("livingSonsAges")}
                />
                <FieldError message={form.formState.errors.livingSonsAges?.message} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="livingDaughtersCount">Number of Living Daughters</Label>
                <Input
                  id="livingDaughtersCount"
                  type="number"
                  {...form.register("livingDaughtersCount")}
                />
                <FieldError
                  message={form.formState.errors.livingDaughtersCount?.message}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="livingDaughtersAges">Living Daughters (ages)</Label>
                <Input
                  id="livingDaughtersAges"
                  placeholder="e.g. 10"
                  {...form.register("livingDaughtersAges")}
                />
                <FieldError
                  message={form.formState.errors.livingDaughtersAges?.message}
                />
              </div>
            </div>
          </FormSectionCard>

          <FormSectionCard
            title="Card 3: Referral Details"
            description="Whether the patient came directly or via another clinician; capture referrer details when external."
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Referral Source</Label>
                <RadioGroup
                  value={referralSource}
                  onValueChange={(v) =>
                    form.setValue("referralSource", v as "self" | "external", {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                  className="flex flex-col gap-2 sm:flex-row sm:gap-6"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="self" id="ref-self" />
                    <Label htmlFor="ref-self">Self-Referral</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="external" id="ref-external" />
                    <Label htmlFor="ref-external">External Reference</Label>
                  </div>
                </RadioGroup>
              </div>

              {referralSource === "external" ? (
                <div className="space-y-2">
                  <Label htmlFor="referringDoctorNameAddress">
                    Referring Doctor Name/Address
                  </Label>
                  <Textarea
                    id="referringDoctorNameAddress"
                    rows={3}
                    {...form.register("referringDoctorNameAddress")}
                  />
                  <FieldError
                    message={
                      form.formState.errors.referringDoctorNameAddress?.message
                    }
                  />
                </div>
              ) : null}
            </div>
          </FormSectionCard>

          <FormSectionCard
            title='Card 4: The "Anandi" AI Insights (Diagnostic Info)'
            description="Ultrasound indications, procedure narrative (may be AI-assisted later), and MTP indication."
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Indication for Ultrasound</Label>
                <ToggleGroup
                  type="multiple"
                  value={selectedIndications}
                  onValueChange={(v) =>
                    form.setValue("indicationForUltrasound", v, {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                  className="flex flex-wrap justify-start gap-2"
                >
                  <ToggleGroupItem value="Estimation of gestational age">
                    Estimation of gestational age
                  </ToggleGroupItem>
                  <ToggleGroupItem value="Fetal growth parameters">
                    Fetal growth parameters
                  </ToggleGroupItem>
                </ToggleGroup>
                <FieldError
                  message={form.formState.errors.indicationForUltrasound?.message as
                    | string
                    | undefined}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="resultOfProcedure">Result of Procedure</Label>
                <Textarea
                  id="resultOfProcedure"
                  rows={4}
                  placeholder="(Auto-filled by AI later)"
                  {...form.register("resultOfProcedure")}
                />
                <FieldError
                  message={form.formState.errors.resultOfProcedure?.message}
                />
              </div>

              <div className="flex items-center justify-between gap-4 rounded-md border p-3">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Indication for MTP</p>
                  <p className="text-xs text-muted-foreground">Yes / No</p>
                </div>
                <Switch
                  checked={form.watch("indicationForMtp")}
                  onCheckedChange={(checked) =>
                    form.setValue("indicationForMtp", checked, {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                />
              </div>
            </div>
          </FormSectionCard>

          <FormSectionCard
            title='Card 5: Digital Sign-off (The "Declarations")'
            description="Procedure date and mandatory confirmations regarding fetal sex disclosure."
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="dateOfProcedure">Date of Procedure</Label>
                <Input
                  id="dateOfProcedure"
                  type="date"
                  {...form.register("dateOfProcedure")}
                />
                <FieldError
                  message={form.formState.errors.dateOfProcedure?.message}
                />
              </div>

              <div className="flex items-start space-x-3 rounded-md border p-3">
                <Checkbox
                  id="patientConsentNoSexDisclosure"
                  checked={form.watch("patientConsentNoSexDisclosure")}
                  onCheckedChange={(v) =>
                    form.setValue("patientConsentNoSexDisclosure", Boolean(v), {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                />
                <div className="space-y-1">
                  <Label htmlFor="patientConsentNoSexDisclosure">
                    I do not want to know the sex of my fetus
                  </Label>
                  <FieldError
                    message={
                      form.formState.errors.patientConsentNoSexDisclosure?.message
                    }
                  />
                </div>
              </div>

              <div className="flex items-start space-x-3 rounded-md border p-3">
                <Checkbox
                  id="doctorConfirmationNoSexDisclosure"
                  checked={form.watch("doctorConfirmationNoSexDisclosure")}
                  onCheckedChange={(v) =>
                    form.setValue("doctorConfirmationNoSexDisclosure", Boolean(v), {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                />
                <div className="space-y-1">
                  <Label htmlFor="doctorConfirmationNoSexDisclosure">
                    I have not disclosed the sex
                  </Label>
                  <FieldError
                    message={
                      form.formState.errors.doctorConfirmationNoSexDisclosure?.message
                    }
                  />
                </div>
              </div>

              <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:justify-end">
                <Button type="submit">Save</Button>
              </div>
            </div>
          </FormSectionCard>
        </form>
      </div>
    </div>
  );
}
