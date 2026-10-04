import { useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, StepProgress, useAction } from "../components/ui";
import { useApp } from "../store";
import { CATEGORIES } from "../types";

export default function ComplaintScreen() {
  const { t, lang, go, session } = useApp();
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState<string>("");
  const [details, setDetails] = useState("");
  const [name, setName] = useState(session?.user?.name.replace(" (demo)", "") ?? "");
  const [society, setSociety] = useState(session?.user?.society_name ?? "");
  const [memberNo, setMemberNo] = useState(session?.user?.member_no ?? "");
  const create = useAction(() => api.complaint({
    category, society_type: "unknown", member_name: name || undefined, society_name: society || undefined,
    member_no: memberNo || undefined, details: details.trim() || undefined }, lang));

  const submit = async () => { const r = await create.run(); if (r) go({ name: "result", view: { kind: "complaint", data: r } }); };
  if (create.busy) return <Shell title={t("makeComplaint")}><Spinner label={t("loading")} /></Shell>;
  return (
    <Shell title={t("makeComplaint")}>
      <StepProgress current={step} total={3} />
      <ErrorBanner message={create.error} />
      {step === 1 && (
        <>
          <h2>{t("category")}</h2>
          <div className="grid">
            {CATEGORIES.map((c) => (
              <BigButton key={c} variant="primary" onClick={() => { setCategory(c); setStep(2); }}>{t(`cat.${c}` as never)}</BigButton>
            ))}
          </div>
        </>
      )}
      {step === 2 && (
        <>
          <h2>{t("details")}</h2>
          <textarea aria-label={t("details")} placeholder={t("detailsHint")} rows={6} maxLength={2000} value={details} onChange={(e) => setDetails(e.target.value)} />
          <BigButton variant="primary" onClick={() => setStep(3)}>{t("next")}</BigButton>
        </>
      )}
      {step === 3 && (
        <>
          <label className="field">{t("members")}<input value={society} maxLength={120} onChange={(e) => setSociety(e.target.value)} /></label>
          <label className="field">{t("name")}<input value={name} maxLength={80} onChange={(e) => setName(e.target.value)} /></label>
          <label className="field">{t("memberNo")}<input value={memberNo} maxLength={30} onChange={(e) => setMemberNo(e.target.value)} /></label>
          <BigButton variant="primary" onClick={() => void submit()}>{t("createComplaint")}</BigButton>
        </>
      )}
      {step > 1 && <BigButton variant="ghost" onClick={() => setStep(step - 1)}>{t("back")}</BigButton>}
    </Shell>
  );
}
