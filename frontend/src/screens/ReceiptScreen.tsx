import { useEffect, useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, useAction } from "../components/ui";
import { useApp } from "../store";
import type { Screen } from "../types";

type Req = Extract<Screen, { name: "receipt" }>["req"];

export default function ReceiptScreen({ req }: { req: Req }) {
  const { t, go } = useApp();
  const [text, setText] = useState<string | null>(null);
  const [done, setDone] = useState<null | boolean>(null);
  const load = useAction(() => api.preview(req));
  const print = useAction(() => api.print(req));

  useEffect(() => { void load.run().then((r) => r && setText(r.receipt)); /* eslint-disable-next-line */ }, []);

  const doPrint = async () => { const r = await print.run(); if (r) setDone(r.printed); };
  if (load.busy) return <Shell title={t("preview")}><Spinner label={t("loading")} /></Shell>;
  return (
    <Shell title={t("preview")}>
      <ErrorBanner message={load.error ?? print.error} onRetry={text === null ? () => void load.run().then((r) => r && setText(r.receipt)) : undefined} />
      {text !== null && <pre className="receipt" aria-label={t("preview")}>{text}</pre>}
      {done === true && <div className="notice ok">✅ {t("printed")}</div>}
      {done === false && <div className="notice">{t("notPrinted")}</div>}
      {print.busy ? <Spinner label={t("loading")} /> : (
        <BigButton icon="🖨️" variant="primary" disabled={text === null || done === true} onClick={() => void doPrint()}>{t("printNow")}</BigButton>
      )}
      <BigButton variant="ghost" onClick={() => go({ name: "home" })}>{t("home")}</BigButton>
    </Shell>
  );
}
