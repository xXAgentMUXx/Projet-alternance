import React from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://localhost:8000";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  return res;
}

function LinkedInSessionUpload() {
  const [file,         setFile]         = React.useState(null);
  const [uploadStatus, setUploadStatus] = React.useState(null);
  const [loading,      setLoading]      = React.useState(false);
  const [hasSession,   setHasSession]   = React.useState(false);

  React.useEffect(() => {
    api("/linkedin-session/status")
      .then((r) => r.json())
      .then((d) => { if (d) setHasSession(d.exists); })
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setUploadStatus(null);
    try {
      const b64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload  = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      const resp = await fetch(`${API_BASE}/linkedin-session/upload`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ content: b64 }),
      });

      if (resp.ok) {
        setUploadStatus("ok");
        setHasSession(true);
        setFile(null);
      } else {
        setUploadStatus("error");
      }
    } catch {
      setUploadStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-4 mt-6">
      <div>
        <h2 className="text-lg font-bold">🔗 Session LinkedIn (StaffSpy)</h2>
        <p className="text-sm text-slate-500 mt-1">
          Génère le fichier session localement puis uploade-le ici pour activer
          la recherche de contacts LinkedIn.
        </p>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Statut :</span>
        {hasSession ? (
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
            ✓ Session active
          </span>
        ) : (
          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
            ✗ Aucune session
          </span>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800 space-y-2">
        <p className="font-semibold">Comment générer session.pkl :</p>
        <pre className="bg-blue-100 rounded-lg px-3 py-2 text-xs font-mono">
pip install staffspy[browser]
        </pre>
        <pre className="bg-blue-100 rounded-lg p-3 text-xs font-mono overflow-x-auto">
{`from staffspy import LinkedInAccount

account = LinkedInAccount(
    session_file="session.pkl"
)

input(
    "Connecte-toi à LinkedIn puis appuie sur Entrée..."
)

print("session.pkl généré !")
`}
        </pre>
        <p className="text-xs">
          Ensuite sélectionne le fichier
          <code className="bg-blue-100 px-1 rounded ml-1">session.pkl</code>.
        </p>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <input
          type="file"
          accept=".pkl"
          onChange={(e) => { setFile(e.target.files[0]); setUploadStatus(null); }}
          className="text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-slate-100"
        />
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Upload..." : "Uploader session.pkl"}
        </button>
      </div>

      {uploadStatus === "ok"    && <p className="text-green-600 font-medium">✅ Session uploadée avec succès !</p>}
      {uploadStatus === "error" && <p className="text-red-600 font-medium">❌ Erreur lors de l'upload.</p>}
    </div>
  );
}

export default function SettingsPage() {
  const navigate = useNavigate();

  const [geminiKey,  setGeminiKey]  = React.useState("");
  const [lbaKey,     setLbaKey]     = React.useState("");
  const [status,     setStatus]     = React.useState(null);
  const [saving,     setSaving]     = React.useState(false);
  const [saved,      setSaved]      = React.useState(false);
  const [showGemini, setShowGemini] = React.useState(false);
  const [showLba,    setShowLba]    = React.useState(false);

  const SCRAPERS = [
    "LinkedIn",
    "Indeed",
    "France Travail",
    "APEC",
    "Meteojob",
    "HelloWork",
    "Bonne Alternance",
    "Greenhouse",
    "Lever",
    "SmartRecruiters",
    "WTTJ",
  ];

  const [autoConfig, setAutoConfig] = React.useState({
    keyword:  "",
    city:     "",
    scrapers: [],
  });

  const [savingAuto, setSavingAuto] = React.useState(false);
  const [savedAuto,  setSavedAuto]  = React.useState(false);

  React.useEffect(() => {
    async function load() {
      try {
        const d1 = await api("/api-keys-config").then((r) => r.json());
        if (d1) setStatus(d1);

        const d2 = await api("/auto-search-config").then((r) => r.json());
        if (d2) setAutoConfig(d2);
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);

  const saveAutoConfig = async () => {
    setSavingAuto(true);
    try {
      await api("/auto-search-config", {
        method: "POST",
        body:   JSON.stringify(autoConfig),
      });
      setSavedAuto(true);
      setTimeout(() => setSavedAuto(false), 3000);
    } catch (e) {
      alert("Erreur : " + e.message);
    } finally {
      setSavingAuto(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const body = {};
      if (geminiKey) body.gemini_api_key = geminiKey;
      if (lbaKey)    body.lba_api_key    = lbaKey;
      await api("/api-keys-config", {
        method: "POST",
        body:   JSON.stringify(body),
      });
      setSaved(true);
      setGeminiKey("");
      setLbaKey("");
      const data = await api("/api-keys-config").then((r) => r.json());
      if (data) setStatus(data);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      alert("Erreur : " + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-xl mx-auto">

        {/* Header */}
        <div className="relative mb-8">
          <button
            onClick={() => navigate(-1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline"
          >
            ← Retour
          </button>
          <h1 className="text-3xl font-bold text-center">Paramètres</h1>
        </div>

        {/* Clés API */}
        <div className="bg-white rounded-2xl shadow p-6 space-y-6">
          <h2 className="text-lg font-bold">Clés API</h2>
          <p className="text-sm text-slate-500 -mt-4">
            Les clés sont stockées localement et ne sont jamais affichées en clair.
          </p>

          {/* Gemini */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-semibold">🤖 Gemini API Key</label>
              {status?.gemini_set && (
                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                  ✓ Configurée
                </span>
              )}
            </div>
            {status?.gemini_set && (
              <p className="text-xs text-slate-400 mb-1">Clé actuelle : {status.gemini_api_key}</p>
            )}
            <div className="relative">
              <input
                type={showGemini ? "text" : "password"}
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder={
                  status?.gemini_set
                    ? "Nouvelle clé (laisser vide pour garder l'actuelle)"
                    : "AIza..."
                }
                className="w-full border rounded-xl px-4 py-2.5 text-sm pr-20"
              />
              <button
                type="button"
                onClick={() => setShowGemini((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600"
              >
                {showGemini ? "Masquer" : "Afficher"}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Obtenir une clé sur{" "}
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="underline">
                Google AI Studio
              </a>
            </p>
          </div>

          {/* LBA */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-semibold">🎓 La Bonne Alternance API Key</label>
              {status?.lba_set && (
                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                  ✓ Configurée
                </span>
              )}
            </div>
            {status?.lba_set && (
              <p className="text-xs text-slate-400 mb-1">Clé actuelle : {status.lba_api_key}</p>
            )}
            <div className="relative">
              <input
                type={showLba ? "text" : "password"}
                value={lbaKey}
                onChange={(e) => setLbaKey(e.target.value)}
                placeholder={
                  status?.lba_set
                    ? "Nouvelle clé (laisser vide pour garder l'actuelle)"
                    : "Votre clé LBA..."
                }
                className="w-full border rounded-xl px-4 py-2.5 text-sm pr-20"
              />
              <button
                type="button"
                onClick={() => setShowLba((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600"
              >
                {showLba ? "Masquer" : "Afficher"}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Obtenir une clé sur{" "}
              <a href="https://labonnealternance.apprentissage.beta.gouv.fr/" target="_blank" rel="noreferrer" className="underline">
                La Bonne Alternance
              </a>
            </p>
          </div>

          {/* Bouton save clés */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleSave}
              disabled={saving || (!geminiKey && !lbaKey)}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-xl hover:bg-blue-700 font-semibold text-sm disabled:opacity-50"
            >
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
            {saved && (
              <span className="text-sm text-emerald-600 font-medium">✅ Clés enregistrées !</span>
            )}
          </div>
        </div>

        <LinkedInSessionUpload />

        {/* Préférences de recherche automatique */}
        <div className="bg-white rounded-2xl shadow p-6 space-y-6 mt-6">
          <h2 className="text-lg font-bold">🤖 Préférences de recherche automatique</h2>

          <div>
            <label className="block text-sm font-semibold mb-2">Mot-clé</label>
            <input
              className="w-full border rounded-xl px-4 py-2"
              value={autoConfig.keyword}
              onChange={(e) => setAutoConfig({ ...autoConfig, keyword: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">Ville</label>
            <input
              className="w-full border rounded-xl px-4 py-2"
              value={autoConfig.city}
              onChange={(e) => setAutoConfig({ ...autoConfig, city: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-3">Scrapers utilisés</label>
            <div className="grid grid-cols-2 gap-3">
              {SCRAPERS.map((scraper) => {
                const isLba      = scraper === "Bonne Alternance";
                const isDisabled = isLba && !status?.lba_set;

                return (
                  <label
                    key={scraper}
                    className={`flex items-center gap-2 ${isDisabled ? "opacity-50 cursor-not-allowed" : ""}`}
                    title={isDisabled ? "Configurez votre clé LBA dans la section Clés API" : ""}
                  >
                    <input
                      type="checkbox"
                      checked={autoConfig.scrapers.includes(scraper)}
                      disabled={isDisabled}
                      onChange={(e) => {
                        if (isDisabled) return;
                        setAutoConfig({
                          ...autoConfig,
                          scrapers: e.target.checked
                            ? [...autoConfig.scrapers, scraper]
                            : autoConfig.scrapers.filter((s) => s !== scraper),
                        });
                      }}
                    />
                    <span>
                      {scraper}
                      {isDisabled && (
                        <span className="text-xs text-slate-400 ml-1">(clé LBA requise)</span>
                      )}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={saveAutoConfig}
              disabled={savingAuto}
              className="bg-blue-600 text-white px-6 py-2 rounded-xl hover:bg-blue-700"
            >
              {savingAuto ? "Enregistrement..." : "Enregistrer"}
            </button>
            {savedAuto && <span className="text-green-600">✅ Préférences enregistrées</span>}
          </div>
        </div>

      </div>
    </div>
  );
}