import { useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, StepProgress, useAction } from "../components/ui";
import { useApp } from "../store";
import { OCCUPATIONS } from "../types";

export default function SchemesScreen() {
  const { t, lang, go } = useApp(); const [step, setStep] = useState(1); const [land, setLand] = useState<boolean | null>(null); const [occ, setOcc] = useState<string[]>([]); const [other, setOther] = useState("");
  const search = useAction((m: boolean | null) => api.schemes({ owns_land: land, occupation: occ, other_occupation: other.trim() || undefined, is_society_member: m }, lang));
  const finish = async (m: boolean | null) => { const r = await search.run(m); if (r) go({ name: "result", view: { kind: "schemes", data: r } }); };
  if (search.busy) return <Shell title={t("findSchemes")}><Spinner label={t("thinking")} /></Shell>;
  const yn = (set: (v: boolean | null) => void, onDone: (v: boolean | null) => void) => <div className="grid">{([[true, t("yes")], [false, t("no")], [null, t("skip")]] as const).map(([v, label]) => <BigButton key={String(v)} variant={v === true ? "primary" : "default"} onClick={() => { set(v); onDone(v); }}>{label}</BigButton>)}</div>;
  const occupationValid = occ.length > 0 || other.trim().length > 0;
  return <Shell title={t("findSchemes")}>
    <StepProgress current={step} total={3} /><ErrorBanner message={search.error} />
    {step === 1 && <><h2>{t("schemeQ1")}</h2>{yn(setLand, () => setStep(2))}</>}
    {step === 2 && <><h2>{t("schemeQ2")}</h2><div className="grid">{OCCUPATIONS.map(o => <button key={o} className="big-btn choice" aria-pressed={occ.includes(o)} onClick={() => setOcc(c => c.includes(o) ? c.filter(x => x !== o) : [...c, o])}>{occ.includes(o) ? "✅ " : ""}{t(`occ.${o}` as never)}</button>)}</div><label className="field">{t("otherOccupation")}<input value={other} onChange={e => setOther(e.target.value)} placeholder={t("otherOccupationHint")} maxLength={100} /></label><BigButton variant="primary" disabled={!occupationValid} onClick={() => setStep(3)}>{t("next")}</BigButton>{!occupationValid && <p className="hint">{t("schemeStep2Required")}</p>}</>}
    {step === 3 && <><h2>{t("schemeQ3")}</h2>{yn(() => undefined, v => void finish(v))}</>}
    {step > 1 && <BigButton variant="ghost" onClick={() => setStep(step - 1)}>{t("back")}</BigButton>}
  </Shell>;
}