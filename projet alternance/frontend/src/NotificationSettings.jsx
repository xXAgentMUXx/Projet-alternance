import React from "react";
import { useNavigate } from "react-router-dom";

const ADDED_PEOPLE_KEY = "addedPeople";

export default function NotificationSettings({ applications = [] }) {
  const navigate = useNavigate();

  // ── État formulaire ──────────────────────────────────────
  const [type,             setType]             = React.useState("discord");
  const [discordWebhook,   setDiscordWebhook]   = React.useState("");
  const [email,            setEmail]            = React.useState("");
  const [gmailUser,        setGmailUser]        = React.useState("");
  const [gmailAppPassword, setGmailAppPassword] = React.useState("");
  const [showPassword,     setShowPassword]     = React.useState(false);

  const [saved,                   setSaved]                   = React.useState(false);
  const [autoSearchNotifications, setAutoSearchNotifications] = React.useState(null);
  const [loadingNotifications,    setLoadingNotifications]    = React.useState(false);
  const [sendingNotification,     setSendingNotification]     = React.useState(false);
  const [sendNotificationStatus,  setSendNotificationStatus]  = React.useState(null);

  // ── Chargement config backend au démarrage ───────────────
  const fetchBackendConfig = async () => {
    try {
      const res = await fetch("http://localhost:8000/notification-config");
      if (!res.ok) return;
      const cfg = await res.json();
      setDiscordWebhook(cfg.discordWebhook || "");
      setEmail(cfg.email || "");
      setGmailUser(cfg.gmailUser || "");
      setGmailAppPassword(cfg.gmailAppPassword || "");
      if (cfg.sendEmail) setType("email");
      else setType("discord");
    } catch (e) {
      console.error("Erreur chargement config :", e);
    }
  };

  const fetchNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const res  = await fetch("http://localhost:8000/notifications");
      const data = await res.json();
      setAutoSearchNotifications(data);
    } catch (e) {
      console.error(e);
      setAutoSearchNotifications(null);
    } finally {
      setLoadingNotifications(false);
    }
  };

  React.useEffect(() => {
    fetchBackendConfig();
    fetchNotifications();
  }, []);

  // ── Sauvegarde ───────────────────────────────────────────
  const handleSave = async () => {
    const payload = {
      discordWebhook:   discordWebhook.trim(),
      email:            email.trim(),
      sendDiscord:      type === "discord",
      sendEmail:        type === "email",
      gmailUser:        gmailUser.trim(),
      gmailAppPassword: gmailAppPassword.trim(),
    };

    try {
      const res = await fetch("http://localhost:8000/notification-config", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      alert("Erreur lors de la sauvegarde : " + e.message);
    }
  };

  // ── Envoi test ───────────────────────────────────────────
  const sendNotification = async () => {
    setSendingNotification(true);
    setSendNotificationStatus(null);

    const payload = {
      total_new_jobs:            summary.total_new_jobs,
      source_results:            summary.source_results,
      follow_up_notifications:   followUpNotifications,
      pending_relance_companies: pendingRelanceCompanies,
      message:                   "Alerte de suivi : nouvelles offres et relances à préparer.",
    };

    try {
      const res  = await fetch("http://localhost:8000/notify", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });
      const data = await res.json();
      setSendNotificationStatus(data);
    } catch (e) {
      console.error(e);
      setSendNotificationStatus({ sentDiscord: false, sentEmail: false, errors: [e.message] });
    } finally {
      setSendingNotification(false);
    }
  };

  // ── Calculs relances ─────────────────────────────────────
  const followUpNotifications = React.useMemo(() => {
    if (!applications?.length) return [];
    const now = new Date();
    return applications
      .filter((app) => app.status === "En cours" && app.followUpDate)
      .map((app) => {
        const due      = new Date(app.followUpDate);
        if (isNaN(due)) return null;
        const daysLeft = Math.ceil((due - now) / (1000 * 60 * 60 * 24));
        if (daysLeft < 0)  return { type: "overdue",  company: app.company || "?", days: Math.abs(daysLeft), followUpDate: app.followUpDate };
        if (daysLeft <= 3) return { type: "due_soon", company: app.company || "?", days: daysLeft,            followUpDate: app.followUpDate };
        return null;
      })
      .filter(Boolean);
  }, [applications]);

  const pendingRelanceCompanies = React.useMemo(() => {
    if (!applications?.length) return [];
    let added = [];
    try { added = JSON.parse(localStorage.getItem(ADDED_PEOPLE_KEY) || "[]"); } catch {}
    const addedSet = new Set(added.map((p) => p.savedForCompany).filter(Boolean));
    return [...new Set(
      applications
        .filter((a) => a.status === "En cours" && a.company)
        .map((a) => a.company)
    )].filter((c) => !addedSet.has(c));
  }, [applications]);

  const summary = autoSearchNotifications || { total_new_jobs: 0, source_results: {}, timestamp: null };

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-3xl mx-auto">

        <div className="relative mb-8">
          <button
            onClick={() => navigate(-1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline"
          >
            ← Retour
          </button>
          <h1 className="text-3xl font-bold text-center">Notifications</h1>
        </div>

        <div className="bg-white rounded-2xl shadow p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
            <div>
              <h2 className="text-xl font-bold">Alertes actives</h2>
              <p className="text-sm text-gray-500">Synthèse des nouvelles offres et relances.</p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={fetchNotifications}
                disabled={loadingNotifications}
                className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {loadingNotifications ? "Chargement…" : "Rafraîchir"}
              </button>
              <button
                onClick={sendNotification}
                disabled={sendingNotification}
                className="px-4 py-2 rounded-xl bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
              >
                {sendingNotification ? "Envoi…" : "Tester l'envoi"}
              </button>
            </div>
          </div>

          {sendNotificationStatus && (
            <div className={`mb-4 rounded-xl p-4 text-sm border ${
              sendNotificationStatus.errors?.length
                ? "bg-red-50 border-red-200 text-red-700"
                : "bg-emerald-50 border-emerald-200 text-emerald-700"
            }`}>
              <p className="font-semibold mb-1">Résultat de l'envoi :</p>
              <p>Discord : {sendNotificationStatus.sentDiscord ? "✅ Envoyé" : "❌ Non envoyé"}</p>
              <p>Email   : {sendNotificationStatus.sentEmail   ? "✅ Envoyé" : "❌ Non envoyé"}</p>
              {sendNotificationStatus.errors?.length > 0 && (
                <p className="mt-1 text-xs">{sendNotificationStatus.errors.join(" · ")}</p>
              )}
            </div>
          )}

          <div className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs text-gray-500 mb-1">Nouvelles offres (recherches automatiques)</p>
              <p className="font-semibold">
                {summary.total_new_jobs > 0
                  ? `${summary.total_new_jobs} nouvelle${summary.total_new_jobs > 1 ? "s" : ""} offre${summary.total_new_jobs > 1 ? "s" : ""}`
                  : "Aucune nouvelle offre récemment."}
              </p>
              {summary.timestamp && (
                <p className="text-xs text-gray-400 mt-1">
                  Dernière recherche : {new Date(summary.timestamp).toLocaleString()}
                </p>
              )}
              {Object.keys(summary.source_results || {}).length > 0 && (
                <div className="mt-3 space-y-2">
                  {Object.entries(summary.source_results).map(([source, stats]) => (
                    <div key={source} className="flex justify-between items-center bg-white rounded-lg px-3 py-2 text-sm border border-slate-100">
                      <span className="font-medium">{source}</span>
                      <span className="text-slate-500">
                        {stats.error ? "⚠️ Erreur" : `${stats.new_jobs} nouvelles / ${stats.total_jobs} totales`}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs text-gray-500 mb-1">Relances à préparer</p>
              {followUpNotifications.length > 0 ? (
                <div className="space-y-2 mt-2">
                  {followUpNotifications.map((alert, i) => (
                    <div key={i} className={`rounded-lg px-3 py-2 text-sm border ${
                      alert.type === "overdue"
                        ? "bg-red-50 border-red-200 text-red-700"
                        : "bg-amber-50 border-amber-200 text-amber-700"
                    }`}>
                      <p className="font-semibold">{alert.company}</p>
                      <p className="text-xs mt-0.5">
                        {alert.type === "overdue"
                          ? `En retard de ${alert.days} jour${alert.days > 1 ? "s" : ""}`
                          : `Dans ${alert.days} jour${alert.days > 1 ? "s" : ""}`}
                        {" · "}{new Date(alert.followUpDate).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 mt-1">Aucune relance urgente.</p>
              )}
            </div>

            {pendingRelanceCompanies.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-gray-500 mb-2">Candidatures sans contact de relance</p>
                <div className="space-y-1">
                  {pendingRelanceCompanies.map((c) => (
                    <div key={c} className="bg-white rounded-lg px-3 py-2 text-sm border border-slate-100 font-medium">{c}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-xl font-bold mb-5">Configuration des notifications</h2>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <button
              onClick={() => setType("discord")}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                type === "discord" ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <p className="text-sm font-semibold">🎮 Discord</p>
              <p className="text-xs text-slate-500 mt-0.5">Via un webhook Discord</p>
            </button>
            <button
              onClick={() => setType("email")}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                type === "email" ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <p className="text-sm font-semibold">📧 Email (Gmail)</p>
              <p className="text-xs text-slate-500 mt-0.5">Via ton compte Gmail</p>
            </button>
          </div>

          <div className="space-y-4">

            {type === "discord" && (
              <>
                <div>
                  <label className="block text-sm font-semibold mb-1">Webhook Discord</label>
                  <input
                    type="text"
                    value={discordWebhook}
                    onChange={(e) => setDiscordWebhook(e.target.value)}
                    placeholder="https://discord.com/api/webhooks/..."
                    className="w-full border rounded-xl px-4 py-2.5 text-sm"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Paramètres du serveur Discord → Intégrations → Webhooks → Copier l'URL
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1">Email destinataire</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ton.email@example.com"
                    className="w-full border rounded-xl px-4 py-2.5 text-sm"
                  />
                </div>
              </>
            )}

            {type === "email" && (
              <>
                <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
                  <p className="font-semibold mb-1">⚠️ Mot de passe d'application requis</p>
                  <p>Gmail bloque les connexions directes. Tu dois créer un <strong>mot de passe d'application</strong> :</p>
                  <ol className="list-decimal ml-4 mt-2 space-y-1 text-xs">
                    <li>Active la <strong>validation en 2 étapes</strong> sur ton compte Google</li>
                    <li>Va sur <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="underline font-medium">myaccount.google.com/apppasswords</a></li>
                    <li>Crée un mot de passe pour "Autre application" → nomme-le "JobScraper"</li>
                    <li>Copie le code à 16 caractères généré et colle-le ci-dessous</li>
                  </ol>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1">Adresse Gmail expéditrice</label>
                  <input
                    type="email"
                    value={gmailUser}
                    onChange={(e) => setGmailUser(e.target.value)}
                    placeholder="ton.adresse@gmail.com"
                    className="w-full border rounded-xl px-4 py-2.5 text-sm"
                  />
                  <p className="text-xs text-slate-400 mt-1">L'adresse Gmail qui enverra les notifications.</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1">Mot de passe d'application Google</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={gmailAppPassword}
                      onChange={(e) => setGmailAppPassword(e.target.value)}
                      placeholder="xxxx xxxx xxxx xxxx"
                      className="w-full border rounded-xl px-4 py-2.5 text-sm pr-12"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
                    >
                      {showPassword ? "Masquer" : "Afficher"}
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Code à 16 caractères généré sur Google. Espaces autorisés.</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1">Email destinataire</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="destinataire@example.com"
                    className="w-full border rounded-xl px-4 py-2.5 text-sm"
                  />
                  <p className="text-xs text-slate-400 mt-1">Peut être la même adresse Gmail ou une autre adresse.</p>
                </div>
              </>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleSave}
                className="bg-blue-600 text-white px-6 py-2.5 rounded-xl hover:bg-blue-700 font-semibold text-sm"
              >
                Enregistrer
              </button>
              {saved && (
                <span className="text-sm text-emerald-600 font-medium">✅ Configuration enregistrée !</span>
              )}
            </div>

            <p className="text-xs text-slate-400 pt-1">
              Les identifiants sont stockés dans <code>notification_config.json</code> sur le serveur (pas dans le navigateur).
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}