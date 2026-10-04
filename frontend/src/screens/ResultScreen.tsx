import { BigButton, Shell } from "../components/ui";
import { useApp } from "../store";
import type { ResultView } from "../types";

function Warn({ ok }: { ok?: boolean }) {
  const { t } = useApp();
  return ok === false ? <div className="notice">{t("translationWarn")}</div> : null;
}

export default function ResultScreen({ view }: { view: ResultView }) {
  const { t, go } = useApp();
  let body: JSX.Element, speak = "", print: (() => void) | null = null;

  if (view.kind === "ask") {
    const d = view.data;
    speak = d.mode === "full" && d.grounded ? d.answer : "";
    if (d.conversation_id) print = () => go({ name: "receipt", req: { kind: "answer", conversation_id: d.conversation_id! } });
    body = (
      <>
        {d.mode === "retrieval_only" && <div className="notice">{t("offlineMode")}</div>}
        {d.mode === "no_evidence" && <div className="notice">{t("noEvidence")}</div>}
        {d.mode === "full" && !d.grounded && <div className="error">⚠️ {t("unverified")}</div>}
        {d.mode !== "retrieval_only" && <div className="card"><p className="big">{d.answer}</p></div>}
        {d.sources.length > 0 && <><h2>{t("sources")}</h2>
          {d.sources.map((s) => (
            <div className="card" key={s.n}><strong>[{s.n}] {s.file}{s.page ? `, p.${s.page}` : ""}{s.section ? ` – ${s.section}` : ""}</strong>
              {d.mode === "retrieval_only" && <p>{s.excerpt}</p>}</div>
          ))}</>}
        <Warn ok={d.translation_ok} />
        <p className="disclaimer">{d.disclaimer}</p>
      </>
    );
  } else if (view.kind === "contract") {
    const d = view.data;
    if (d.conversation_id) print = () => go({ name: "receipt", req: { kind: "answer", conversation_id: d.conversation_id! } });
    speak = d.findings.map((f) => `${f.title}. ${f.explanation}`).join(" ");
    body = (
      <>
        <div className={`card badge ${d.risk_level}`}><p className="big">{t("riskLevel")}: {d.risk_level.toUpperCase()}</p></div>
        {d.findings.length === 0 && <p className="big">{t("noRisks")}</p>}
        {d.findings.map((f, i) => (
          <div className={`card sev-${f.severity}`} key={i}><h3>{f.title}</h3><blockquote>{f.clause}</blockquote><p>{f.explanation}</p></div>
        ))}
        <Warn ok={d.translation_ok} /><p className="disclaimer">{d.disclaimer}</p>
      </>
    );
  } else if (view.kind === "notice") {
    const d = view.data;
    if (d.conversation_id) print = () => go({ name: "receipt", req: { kind: "answer", conversation_id: d.conversation_id! } });
    const label = { likely_fraud: t("likelyFraud"), suspicious: t("suspicious"), low_concern: t("lowConcern"), no_flags: t("noFlags") }[d.verdict];
    speak = [label, ...d.advice].join(". ");
    body = (
      <>
        <div className={`card badge ${d.verdict}`}><p className="big">{label}</p></div>
        {d.flags.map((f, i) => <div className="card" key={i}><h3>{f.title}</h3><p>{f.explanation}</p></div>)}
        {d.advice.length > 0 && <ul className="advice">{d.advice.map((a, i) => <li key={i}>{a}</li>)}</ul>}
        <Warn ok={d.translation_ok} /><p className="disclaimer">{d.disclaimer}</p>
      </>
    );
  } else if (view.kind === "schemes") {
    const d = view.data;
    if (d.conversation_id) print = () => go({ name: "receipt", req: { kind: "answer", conversation_id: d.conversation_id! } });
    speak = d.schemes.map((s) => `${s.name}. ${s.summary}`).join(" ");
    body = (
      <>
        {d.schemes.map((s) => (
          <div className={`card ${s.status}`} key={s.id}>
            <h3>{s.name} <span className="tag">{s.status === "likely_eligible" ? t("eligible") : t("checkDetails")}</span></h3>
            <p>{s.summary}</p>
            {s.documents.length > 0 && <p><strong>{t("documentsNeeded")}:</strong> {s.documents.join(", ")}</p>}
            <p><strong>{t("whereApply")}:</strong> {s.where_to_apply}</p>
            {!s.verified && <p className="muted">⚠️ {t("notVerified")}</p>}
          </div>
        ))}
        <p className="disclaimer">{d.note}</p><Warn ok={d.translation_ok} /><p className="disclaimer">{d.disclaimer}</p>
      </>
    );
  } else {
    const d = view.data;
    print = () => go({ name: "receipt", req: { kind: "complaint", complaint_id: d.id } });
    speak = d.guide.steps.map((s) => `${s.title}. ${s.detail}`).join(" ");
    body = (
      <>
        <div className="card"><p>{t("reference")}</p><p className="big">{d.reference}</p></div>
        <h2>{t("steps")}</h2>
        {d.guide.steps.map((s) => (
          <div className="card step" key={s.n}><span className="num">{s.n}</span><div><h3>{s.title}</h3><p>{s.detail}</p></div></div>
        ))}
        <p className="disclaimer">{d.guide.note}</p><Warn ok={d.translation_ok} /><p className="disclaimer">{d.guide.disclaimer}</p>
      </>
    );
  }

  return (
    <Shell title={t("result")} speak={speak}>
      {body}
      {print && <BigButton icon="🖨️" variant="primary" onClick={print}>{t("printReceipt")}</BigButton>}
      <BigButton variant="ghost" onClick={() => go({ name: "home" })}>{t("home")}</BigButton>
    </Shell>
  );
}
