import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, useAction } from "../components/ui";
import { useApp } from "../store";

export default function LoginScreen() {
  const { t, lang, login, go } = useApp(); const [manual, setManual] = useState("");
  const rfid = useAction((uid: string) => api.loginRfid(uid, lang)); const fp = useAction(() => api.loginFingerprint(lang)); const guest = useAction(() => api.loginGuest(lang)); const buf = useRef({ text: "", last: 0 });
  const doRfid = async (uid: string) => { const r = await rfid.run(uid.trim()); if (r) login(r); };
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if ((e.target as HTMLElement).tagName === "INPUT") return; const now = Date.now(); if (now - buf.current.last > 100) buf.current.text = ""; buf.current.last = now; if (e.key === "Enter") { const v = buf.current.text; buf.current.text = ""; if (v.length >= 3) void doRfid(v); } else if (e.key.length === 1) buf.current.text += e.key; }; window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey); }, [lang]);
  const busy = rfid.busy || fp.busy || guest.busy; const error = rfid.error ?? fp.error ?? guest.error;
  return <Shell title={t("login")} back={false} speak={t("loginHint")}>
    {busy ? <Spinner label={t("loading")} /> : <>
      <p className="hint">{t("loginHint")}</p><ErrorBanner message={error} />
      <div className="card center"><div className="pulse">💳</div><p className="big">{t("tapCard")}</p></div>
      <BigButton icon="☝️" variant="primary" onClick={async () => { const r = await fp.run(); if (r) login(r); }}>{t("fingerprint")}</BigButton>
      <div className="row"><input aria-label={t("orTypeCard")} placeholder={t("orTypeCard")} value={manual} maxLength={64} onChange={e => setManual(e.target.value.replace(/[^A-Za-z0-9:_-]/g, ""))} /><BigButton disabled={manual.length < 3} onClick={() => void doRfid(manual)}>{t("submit")}</BigButton></div>
      <BigButton variant="primary" onClick={() => go({ name: "register" })}>{t("registerNewUser")}</BigButton>
      <p className="hint">{t("registrationApprovalHint")}</p>
      <BigButton variant="ghost" onClick={() => go({ name: "language" })}>{t("back")}</BigButton>
    </>}
  </Shell>;
}