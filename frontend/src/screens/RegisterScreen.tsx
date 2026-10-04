import { useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, useAction } from "../components/ui";
import { useApp } from "../store";

export default function RegisterScreen() {
  const { t, lang, back } = useApp();
  const [name, setName] = useState(""); const [phone, setPhone] = useState(""); const [address, setAddress] = useState("");
  const [profession, setProfession] = useState(""); const [landOwned, setLandOwned] = useState<boolean | null>(null); const [landArea, setLandArea] = useState(""); const [society, setSociety] = useState(""); const [done, setDone] = useState(false);
  const register = useAction(() => api.register({ name: name.trim(), phone: phone.trim(), address: address.trim(), profession: profession.trim(), land_owned: landOwned === true, land_area: landArea.trim() || undefined, society_name: society.trim() || undefined }, lang));
  const submit = async () => { const r = await register.run(); if (r) setDone(true); };
  if (register.busy) return <Shell title={t("register")}><Spinner label={t("loading")} /></Shell>;
  return <Shell title={t("register")}>
    {done ? <><div className="notice ok"><h2>{t("registrationSubmitted")}</h2><p>{t("registrationPending")}</p></div><BigButton variant="primary" onClick={back}>{t("backToLogin")}</BigButton></> : <>
      <p className="hint">{t("registerHint")}</p><ErrorBanner message={register.error} />
      <label className="field">{t("name")}<input value={name} onChange={e => setName(e.target.value)} maxLength={100} /></label>
      <label className="field">{t("phone")}<input value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g, ""))} maxLength={15} /></label>
      <label className="field">{t("address")}<textarea value={address} onChange={e => setAddress(e.target.value)} rows={3} maxLength={300} /></label>
      <label className="field">{t("profession")}<input value={profession} onChange={e => setProfession(e.target.value)} maxLength={100} /></label>
      <div className="field"><span>{t("landOwned")}</span><div className="row"><BigButton variant={landOwned === true ? "primary" : "default"} onClick={() => setLandOwned(true)}>{t("yes")}</BigButton><BigButton variant={landOwned === false ? "primary" : "default"} onClick={() => setLandOwned(false)}>{t("no")}</BigButton></div></div>
      {landOwned === true && <label className="field">{t("landArea")}<input value={landArea} onChange={e => setLandArea(e.target.value)} maxLength={50} /></label>}
      <label className="field">{t("members")}<input value={society} onChange={e => setSociety(e.target.value)} maxLength={120} /></label>
      <BigButton variant="primary" disabled={!name.trim() || phone.length < 10 || !address.trim() || !profession.trim() || landOwned === null} onClick={() => void submit()}>{t("register")}</BigButton>
      <BigButton variant="ghost" onClick={back}>{t("back")}</BigButton>
    </>}
  </Shell>;
}