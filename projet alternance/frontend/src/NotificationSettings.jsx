import React from "react";
import { useNavigate } from "react-router-dom";

const STORAGE_KEY = "notificationSettings";
const ADDED_PEOPLE_KEY = "addedPeople";

export default function NotificationSettings({ applications = [] }) {
  const navigate = useNavigate();
  const [type, setType] = React.useState("discord");
  const [discordWebhook, setDiscordWebhook] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [saved, setSaved] = React.useState(false);
  const [autoSearchNotifications, setAutoSearchNotifications] = React.useState(null);
  const [loadingNotifications, setLoadingNotifications] = React.useState(false);
  const [sendingNotification, setSendingNotification] = React.useState(false);
  const [sendNotificationStatus, setSendNotificationStatus] = React.useState(null);

  const loadConfig = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { type: "discord", discordWebhook: "", email: "" };
      return JSON.parse(raw);
    } catch (e) {
      return { type: "discord", discordWebhook: "", email: "" };
    }
  };

  const saveConfig = (config) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch (e) {
      console.error(e);
    }
  };

  const loadAddedPeople = () => {
    try {
      const raw = localStorage.getItem(ADDED_PEOPLE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  };

  const fetchBackendConfig = async () => {
    try {
      const response = await fetch("http://localhost:8000/notification-config");
      if (!response.ok) throw new Error("Impossible de charger la config backend");
      const backendConfig = await response.json();
      setDiscordWebhook(backendConfig.discordWebhook || "");
      setEmail(backendConfig.email || "");
      if (backendConfig.sendDiscord) setType("discord");
      else if (backendConfig.sendEmail) setType("email");
      return backendConfig;
    } catch (error) {
      console.error(error);
      return null;
    }
  };

  React.useEffect(() => {
    const savedConfig = loadConfig();
    if (savedConfig.type) setType(savedConfig.type);
    setDiscordWebhook(savedConfig.discordWebhook || "");
    setEmail(savedConfig.email || "");
    fetchBackendConfig();
    fetchNotifications();
  }, []);

  const handleSave = async () => {
    const payload = {
      discordWebhook: discordWebhook.trim(),
      email: email.trim(),
      sendDiscord: type === "discord",
      sendEmail: type === "email",
    };

    try {
      await fetch("http://localhost:8000/notification-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error(error);
    }

    saveConfig({ type, discordWebhook: payload.discordWebhook, email: payload.email });
    setSaved(true);
    window.setTimeout(() => setSaved(false), 3000);
  };

  const fetchNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const response = await fetch("http://localhost:8000/notifications");
      const data = await response.json();
      setAutoSearchNotifications(data);
    } catch (error) {
      console.error(error);
      setAutoSearchNotifications(null);
    } finally {
      setLoadingNotifications(false);
    }
  };

  const sendNotification = async () => {
    setSendingNotification(true);
    setSendNotificationStatus(null);

    const payload = {
      total_new_jobs: summary.total_new_jobs,
      source_results: summary.source_results,
      follow_up_notifications: followUpNotifications,
      pending_relance_companies: pendingRelanceCompanies,
      message: "Alerte de suivi : nouvelles offres et relances à préparer.",
    };

    try {
      const response = await fetch("http://localhost:8000/notify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      setSendNotificationStatus(data);

      if (!response.ok || data.errors?.length) {
        throw new Error(data.errors?.join(", ") || "Erreur lors de l'envoi");
      }

      alert("Notification envoyée avec succès.");
    } catch (error) {
      console.error(error);
      alert("Erreur envoi notification : " + error.message);
    } finally {
      setSendingNotification(false);
    }
  };

  const followUpNotifications = React.useMemo(() => {
    if (!applications?.length) return [];

    const now = new Date();

    return applications
      .filter((app) => app.status === "En cours" && app.followUpDate)
      .map((app) => {
        const dueDate = new Date(app.followUpDate);
        if (Number.isNaN(dueDate.getTime())) return null;

        const diffMillis = dueDate.getTime() - now.getTime();
        const daysLeft = Math.ceil(diffMillis / (1000 * 60 * 60 * 24));

        if (daysLeft < 0) {
          return {
            type: "overdue",
            company: app.company || "Entreprise inconnue",
            days: Math.abs(daysLeft),
            followUpDate: app.followUpDate,
          };
        }

        if (daysLeft <= 3) {
          return {
            type: "due_soon",
            company: app.company || "Entreprise inconnue",
            days: daysLeft,
            followUpDate: app.followUpDate,
          };
        }

        return null;
      })
      .filter(Boolean);
  }, [applications]);

  const pendingRelanceCompanies = React.useMemo(() => {
    if (!applications?.length) return [];

    const addedCompanies = new Set(
      loadAddedPeople()
        .map((person) => person.savedForCompany)
        .filter(Boolean)
    );

    return Array.from(
      new Set(
        applications
          .filter((app) => app.status === "En cours" && app.company)
          .map((app) => app.company)
      )
    ).filter((company) => !addedCompanies.has(company));
  }, [applications]);

  const summary = autoSearchNotifications || {
    total_new_jobs: 0,
    source_results: {},
    timestamp: null,
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="relative mb-8">
          <button
            onClick={() => navigate(-1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline"
          >
            ← Retour
          </button>
          <h1 className="text-3xl font-bold text-center">Notifications</h1>
        </div>

        <div className="bg-white rounded-2xl shadow p-6 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-bold">Alertes actives</h2>
              <p className="text-gray-500">Synthèse des nouvelles offres et des relances à préparer.</p>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <button
                className="rounded-xl border border-blue-600 bg-blue-600 px-5 py-3 text-white hover:bg-blue-700 disabled:opacity-50"
                onClick={fetchNotifications}
                disabled={loadingNotifications}
              >
                {loadingNotifications ? "Rafraîchir..." : "Rafraîchir"}
              </button>
              <button
                className="rounded-xl border border-green-600 bg-green-600 px-5 py-3 text-white hover:bg-green-700 disabled:opacity-50"
                onClick={sendNotification}
                disabled={sendingNotification}
              >
                {sendingNotification ? "Envoi en cours..." : "Tester l'envoi"}
              </button>
            </div>
            {sendNotificationStatus && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold">Résultat d'envoi :</p>
                <p>Discord : {sendNotificationStatus.sentDiscord ? "OK" : "Non"}</p>
                <p>Email : {sendNotificationStatus.sentEmail ? "OK" : "Non"}</p>
                {sendNotificationStatus.errors?.length > 0 && (
                  <p className="text-red-600">{sendNotificationStatus.errors.join("; ")}</p>
                )}
              </div>
            )}
          </div>

          <div className="grid gap-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-gray-500">Nouvelles offres issues des recherches automatiques</p>
              <p className="mt-3 text-xl font-semibold">
                {summary.total_new_jobs > 0
                  ? `${summary.total_new_jobs} nouvelle${summary.total_new_jobs > 1 ? "s" : ""} offre${summary.total_new_jobs > 1 ? "s" : ""} détectée${summary.total_new_jobs > 1 ? "s" : ""}`
                  : "Aucune nouvelle offre détectée récemment."}
              </p>
              {summary.timestamp && (
                <p className="mt-2 text-sm text-gray-500">
                  Dernière recherche automatique : {new Date(summary.timestamp).toLocaleString()}
                </p>
              )}

              {Object.keys(summary.source_results || {}).length > 0 && (
                <div className="mt-4 space-y-3">
                  {Object.entries(summary.source_results).map(([source, stats]) => (
                    <div key={source} className="rounded-xl border border-slate-200 bg-white p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{source}</p>
                        <span className="text-sm text-slate-500">
                          {stats.error ? "Erreur" : `${stats.new_jobs} nouvelles / ${stats.total_jobs} totales`}
                        </span>
                      </div>
                      {stats.error && stats.message && (
                        <p className="mt-2 text-xs text-red-600">{stats.message}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-gray-500">Relances de candidatures à préparer</p>
              {followUpNotifications.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {followUpNotifications.map((alert, index) => (
                    <div key={`${alert.company}-${index}`} className="rounded-xl bg-white p-4 shadow-sm">
                      <p className="font-semibold">{alert.company}</p>
                      <p className="text-sm text-slate-600 mt-1">
                        {alert.type === "overdue"
                          ? `Relance en retard de ${alert.days} jour${alert.days > 1 ? "s" : ""}.`
                          : `Relance dans ${alert.days} jour${alert.days > 1 ? "s" : ""}.`}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">Date prévue : {new Date(alert.followUpDate).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-gray-600">Aucune relance urgente détectée pour le moment.</p>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm text-gray-500">Candidatures sans contacts ajoutés à la relance</p>
              {pendingRelanceCompanies.length > 0 ? (
                <ul className="mt-4 space-y-2">
                  {pendingRelanceCompanies.map((company) => (
                    <li key={company} className="rounded-xl bg-white p-4 shadow-sm">
                      <p className="font-semibold">{company}</p>
                      <p className="text-sm text-slate-600 mt-1">Ajoute des personnes à relancer pour cette entreprise.</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-gray-600">Toutes les candidatures en cours ont au moins un contact de relance.</p>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">Configuration des notifications</h2>

          <div className="grid grid-cols-1 gap-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => setType("discord")}
                className={`rounded-2xl border px-4 py-3 text-left ${type === "discord" ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white"}`}
              >
                <div className="text-sm font-semibold">Discord</div>
                <div className="text-xs text-slate-500">Recevoir les alertes via un webhook Discord.</div>
              </button>
              <button
                type="button"
                onClick={() => setType("email")}
                className={`rounded-2xl border px-4 py-3 text-left ${type === "email" ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white"}`}
              >
                <div className="text-sm font-semibold">Email</div>
                <div className="text-xs text-slate-500">Recevoir les alertes par email.</div>
              </button>
            </div>

            <div className="space-y-3">
              <label className="block text-sm font-semibold">Type de notification</label>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                {type === "discord"
                  ? "Le système enverra des notifications à ton webhook Discord configuré ci-dessous."
                  : "Le système enverra des notifications à l'adresse email configurée ci-dessous."}
              </div>
            </div>

            {type === "discord" ? (
              <div className="space-y-2">
                <label className="block font-semibold">Webhook Discord</label>
                <input
                  type="text"
                  value={discordWebhook}
                  onChange={(e) => setDiscordWebhook(e.target.value)}
                  placeholder="https://discord.com/api/webhooks/..."
                  className="w-full border rounded-2xl px-4 py-3"
                />
                <p className="text-xs text-slate-500">Colle l'URL du webhook Discord qui recevra les notifications.</p>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block font-semibold">Adresse email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ton.email@example.com"
                  className="w-full border rounded-2xl px-4 py-3"
                />
                <p className="text-xs text-slate-500">L'email qui recevra les alertes de recherche d'alternance.</p>
              </div>
            )}

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <div className="font-semibold">Note</div>
              <p>Cette configuration est enregistrée localement dans ton navigateur.</p>
              <p>Le backend peut aussi envoyer les notifications vers Discord ou email.</p>
              <p>Pour l'email, le serveur doit être configuré avec des variables SMTP côté backend.</p>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <button
                onClick={handleSave}
                className="bg-blue-600 text-white px-5 py-3 rounded-2xl hover:bg-blue-700"
              >
                Enregistrer
              </button>
              {saved && (
                <span className="text-sm text-emerald-600">Configuration enregistrée !</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
