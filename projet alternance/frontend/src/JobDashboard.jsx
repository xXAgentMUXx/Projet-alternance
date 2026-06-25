import React from "react";
import { useNavigate } from "react-router-dom";

const SOURCE_COLORS = {
  offres_emploi_lba:  "bg-blue-100 text-blue-700",
  recruteur_lba:      "bg-emerald-100 text-emerald-700",
  "France Travail":   "bg-orange-100 text-orange-700",
  HelloWork:          "bg-cyan-100 text-cyan-700",
  Greenhouse:         "bg-green-100 text-green-700",
  Lever:              "bg-violet-100 text-violet-700",
  WTTJ:               "bg-yellow-100 text-yellow-700",
  SmartRecruiters:    "bg-sky-100 text-sky-700",
  PASS:               "bg-purple-100 text-purple-700",
  default:            "bg-gray-100 text-gray-600",
};

const EMPTY_JOBS = {
  LinkedIn:           [],
  Indeed:             [],
  "Bonne Alternance": [],
  Meteojob:           [],
  APEC:               [],
  HelloWork:          [],
  "France Travail":   [],
  Greenhouse:         [],
  Lever:              [],
  WTTJ:               [],
  SmartRecruiters:    [],
};

const API_BASE_URL = "http://localhost:8000";
const BOARDS_STORAGE_KEY = "jobDashboard.boardsConfig";

const EMPTY_BOARDS_CONFIG = {
  greenhouse_boards: [],
  lever_boards: [],
  smartrecruiters_companies: ["BoschGroup"],
};

const loadBoardsConfig = () => {
  try {
    const stored = JSON.parse(localStorage.getItem(BOARDS_STORAGE_KEY) || "{}");
    return {
      greenhouse_boards: Array.isArray(stored.greenhouse_boards) ? stored.greenhouse_boards : [],
      lever_boards: Array.isArray(stored.lever_boards) ? stored.lever_boards : [],
      smartrecruiters_companies: Array.isArray(stored.smartrecruiters_companies) ? stored.smartrecruiters_companies : EMPTY_BOARDS_CONFIG.smartrecruiters_companies,
    };
  } catch {
    return EMPTY_BOARDS_CONFIG;
  }
};

const saveBoardsConfig = (config) => {
  localStorage.setItem(BOARDS_STORAGE_KEY, JSON.stringify(config));
};

function SourceBadge({ source, type }) {
  const label  = type === "spontanee" ? "Candidature spontanée" : source;
  const colors = SOURCE_COLORS[source] || SOURCE_COLORS.default;
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors}`}>
      {label}
    </span>
  );
}

function JobCard({ job, existing, onClick }) {
  return (
    <div
      onClick={onClick}
      className={
        "p-3 border rounded-xl cursor-pointer hover:bg-slate-50 transition space-y-1" +
        (job.is_new ? " border-l-4 border-l-emerald-400" : "")
      }
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          {job.is_new && (
            <span className="shrink-0 text-xs font-bold bg-emerald-500 text-white px-1.5 py-0.5 rounded-full">
              NEW
            </span>
          )}
          <h3 className="font-semibold text-sm leading-tight truncate">
            {job.title || "Entreprise à contacter"}
          </h3>
        </div>
        <SourceBadge source={job.source} type={job.type} />
      </div>

      {job.company && <p className="text-sm text-gray-600">{job.company}</p>}
      <p className="text-xs text-gray-400">{job.location}</p>

      {(job.contract?.length > 0 || job.remote) && (
        <p className="text-xs text-indigo-500">
          {job.contract?.join(", ")}
          {job.remote && job.remote !== "onsite"
            ? ` · ${job.remote === "remote" ? "Télétravail" : "Hybride"}`
            : ""}
        </p>
      )}

      {job.created_at && (
        <p className="text-xs text-gray-400">📅 {job.created_at}</p>
      )}

      {existing && (
        <p className="text-xs text-gray-500 font-semibold">
          ✓ Déjà postulé{existing.status ? ` — ${existing.status}` : ""}
        </p>
      )}
    </div>
  );
}

function JobModal({ job, existing, getTimeAgo, onApply, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">

        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2 flex-1 pr-4">
            {job.is_new && (
              <span className="shrink-0 text-xs font-bold bg-emerald-500 text-white px-2 py-0.5 rounded-full">
                NEW
              </span>
            )}
            <h2 className="text-xl font-bold leading-tight">
              {job.title || "Candidature spontanée"}
            </h2>
          </div>
          <SourceBadge source={job.source} type={job.type} />
        </div>

        {job.company && <p className="text-lg font-medium text-gray-700">{job.company}</p>}
        <p className="text-gray-400 text-sm mb-1">{job.location}</p>

        {(job.contract?.length > 0 || job.remote) && (
          <p className="text-sm text-indigo-600 mb-1">
            {job.contract?.join(", ")}
            {job.remote && job.remote !== "onsite"
              ? ` · ${job.remote === "remote" ? "Télétravail" : "Hybride"}`
              : ""}
          </p>
        )}

        {job.created_at && (
          <p className="text-sm text-gray-400 mb-2">📅 Publié le {job.created_at}</p>
        )}

        {job.type === "spontanee" && (
          <div className="bg-emerald-50 rounded-xl p-3 mb-3 text-sm space-y-1">
            {job.size    && <p>👥 <span className="text-gray-600">{job.size} salariés</span></p>}
            {job.opco    && <p>🏦 <span className="text-gray-600">OPCO : {job.opco}</span></p>}
            {job.website && (
              <p>🌐 <a href={job.website} target="_blank" rel="noreferrer" className="text-blue-600 underline">{job.website}</a></p>
            )}
            {job.siret   && <p className="text-gray-400 text-xs">SIRET : {job.siret}</p>}
          </div>
        )}

        <p className="text-sm text-gray-600 mb-4 whitespace-pre-line">
          {job.description || "Pas de description disponible."}
        </p>

        {job.phone && (
          <p className="text-sm mb-4">
            📞 <a href={`tel:${job.phone}`} className="text-blue-600">{job.phone}</a>
          </p>
        )}

        {existing && (
          <p className="text-sm text-green-600 font-semibold mb-4">
            ✓ Vous avez candidaté il y a {getTimeAgo(existing.appliedDate)}
          </p>
        )}

        <div className="flex gap-3 flex-wrap">
          {job.url && (
            <button
              onClick={() => onApply(job)}
              className="bg-green-600 text-white px-5 py-2 rounded-xl hover:bg-green-700"
            >
              Postuler
            </button>
          )}
          {job.type === "spontanee" && !job.url && job.phone && (
            <a href={`tel:${job.phone}`} className="bg-blue-600 text-white px-5 py-2 rounded-xl hover:bg-blue-700">
              Appeler
            </a>
          )}
          <button onClick={onClose} className="bg-red-500 text-white px-5 py-2 rounded-xl hover:bg-red-600">
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

function BoardsConfigModal({ initialConfig, onSave, onClose }) {
  const [ghBoards,  setGhBoards]  = React.useState(initialConfig.greenhouse_boards || []);
  const [lvBoards,  setLvBoards]  = React.useState(initialConfig.lever_boards || []);
  const [srCompanies, setSrCompanies] = React.useState(initialConfig.smartrecruiters_companies || []);
  const [ghInput,   setGhInput]   = React.useState("");
  const [lvInput,   setLvInput]   = React.useState("");
  const [srInput,   setSrInput]   = React.useState("");
  const [saving,    setSaving]    = React.useState(false);
  const [saved,     setSaved]     = React.useState(false);

  const parseSmartRecruitersCompany = (value) => {
    const text = value.trim();
    const match = text.match(/smartrecruiters\.com\/([^/?#]+)/i);
    return (match ? match[1] : text).trim();
  };

  const addGh = () => {
    const url = ghInput.trim();
    if (!url.startsWith("https://boards.greenhouse.io/")) {
      alert("URL invalide : doit commencer par https://boards.greenhouse.io/");
      return;
    }
    if (!ghBoards.includes(url)) setGhBoards((p) => [...p, url]);
    setGhInput("");
  };

  const addLv = () => {
    const url = lvInput.trim();
    if (!url.startsWith("https://jobs.lever.co/")) {
      alert("URL invalide : doit commencer par https://jobs.lever.co/");
      return;
    }
    if (!lvBoards.includes(url)) setLvBoards((p) => [...p, url]);
    setLvInput("");
  };

  const addSr = () => {
    const company = parseSmartRecruitersCompany(srInput);
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(company)) {
      alert("Slug SmartRecruiters invalide. Exemple : BoschGroup ou https://jobs.smartrecruiters.com/BoschGroup/...");
      return;
    }
    if (!srCompanies.includes(company)) setSrCompanies((p) => [...p, company]);
    setSrInput("");
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        greenhouse_boards: ghBoards,
        lever_boards: lvBoards,
        smartrecruiters_companies: srCompanies,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      alert("Erreur lors de la sauvegarde : " + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-1">Configurer les boards</h2>
        <p className="text-sm text-gray-500 mb-5">
          Ajoute les pages careers Greenhouse et Lever que tu veux scraper.
        </p>

        <div className="mb-5">
          <label className="block text-sm font-semibold mb-2">
            🟢 Greenhouse <span className="font-normal text-gray-400">(boards.greenhouse.io/…)</span>
          </label>
          <div className="flex gap-2 mb-2">
            <input
              value={ghInput}
              onChange={(e) => setGhInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addGh()}
              placeholder="https://boards.greenhouse.io/example"
              className="flex-1 border rounded-xl px-3 py-2 text-sm"
            />
            <button onClick={addGh} className="bg-green-600 text-white px-3 py-2 rounded-xl text-sm hover:bg-green-700">
              +
            </button>
          </div>
          {ghBoards.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Aucun board configuré</p>
          ) : (
            <div className="space-y-1">
              {ghBoards.map((url) => (
                <div key={url} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-1.5 text-xs">
                  <span className="truncate text-gray-700">{url}</span>
                  <button onClick={() => setGhBoards((p) => p.filter((u) => u !== url))} className="ml-2 text-red-500 hover:text-red-700 shrink-0">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold mb-2">
            🟣 Lever <span className="font-normal text-gray-400">(jobs.lever.co/…)</span>
          </label>
          <div className="flex gap-2 mb-2">
            <input
              value={lvInput}
              onChange={(e) => setLvInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addLv()}
              placeholder="https://jobs.lever.co/example"
              className="flex-1 border rounded-xl px-3 py-2 text-sm"
            />
            <button onClick={addLv} className="bg-violet-600 text-white px-3 py-2 rounded-xl text-sm hover:bg-violet-700">
              +
            </button>
          </div>
          {lvBoards.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Aucun board configuré</p>
          ) : (
            <div className="space-y-1">
              {lvBoards.map((url) => (
                <div key={url} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-1.5 text-xs">
                  <span className="truncate text-gray-700">{url}</span>
                  <button onClick={() => setLvBoards((p) => p.filter((u) => u !== url))} className="ml-2 text-red-500 hover:text-red-700 shrink-0">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold mb-2">
            SmartRecruiters <span className="font-normal text-gray-400">(slug ou jobs.smartrecruiters.com/...)</span>
          </label>
          <div className="flex gap-2 mb-2">
            <input
              value={srInput}
              onChange={(e) => setSrInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSr()}
              placeholder="BoschGroup"
              className="flex-1 border rounded-xl px-3 py-2 text-sm"
            />
            <button onClick={addSr} className="bg-sky-600 text-white px-3 py-2 rounded-xl text-sm hover:bg-sky-700">
              +
            </button>
          </div>
          {srCompanies.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Aucune entreprise configuree</p>
          ) : (
            <div className="space-y-1">
              {srCompanies.map((company) => (
                <div key={company} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-1.5 text-xs">
                  <span className="truncate text-gray-700">{company}</span>
                  <button onClick={() => setSrCompanies((p) => p.filter((c) => c !== company))} className="ml-2 text-red-500 hover:text-red-700 shrink-0">x</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-3 items-center">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 font-semibold text-sm disabled:opacity-50"
          >
            {saving ? "Enregistrement…" : "Enregistrer"}
          </button>
          <button onClick={onClose} className="text-sm text-gray-500 hover:text-gray-700">
            Annuler
          </button>
          {saved && <span className="text-sm text-emerald-600 font-medium">✅ Sauvegardé !</span>}
        </div>
      </div>
    </div>
  );
}

export default function JobDashboard({
  applications,
  setApplications,
  blockedCompanies,
  setBlockedCompanies,
}) {
  const navigate = useNavigate();

  const [jobs,            setJobs]            = React.useState(EMPTY_JOBS);
  const [selectedJob,     setSelectedJob]     = React.useState(null);
  const [keyword,         setKeyword]         = React.useState("");
  const [city,            setCity]            = React.useState("");
  const [loading,         setLoading]         = React.useState(false);
  const [filterType,      setFilterType]      = React.useState("tout");
  const [showBoardsModal, setShowBoardsModal] = React.useState(false);
  const [boardsConfig,    setBoardsConfig]    = React.useState(loadBoardsConfig);

  const [schedulerStatus, setSchedulerStatus] = React.useState({
    nextRunTime:   null,
    countdown:     null,
    autoRunning:   false,
    manualEnabled: true,
  });

  const prevAutoRunning = React.useRef(false);

  const addBusinessDays = (date, days) => {
    let result = new Date(date);
    let added  = 0;
    while (added < days) {
      result.setDate(result.getDate() + 1);
      const day = result.getDay();
      if (day !== 0 && day !== 6) added++;
    }
    return result;
  };

  const formatCountdown = (seconds) => {
    if (seconds === null || seconds === undefined) return "--:--:--";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  };

  const getTimeAgo = (dateString) => {
    const diffDays = Math.floor((new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24));
    if (diffDays < 30) return `${diffDays} jour${diffDays > 1 ? "s" : ""}`;
    return `${Math.floor(diffDays / 30)} mois`;
  };

  const toArray = (v) => (Array.isArray(v) ? v : []);

  const normalizeJobs = (data) => {
    if (!data || typeof data !== "object") return EMPTY_JOBS;
    return {
      LinkedIn:           toArray(data.LinkedIn),
      Indeed:             toArray(data.Indeed),
      "Bonne Alternance": toArray(data["Bonne Alternance"]),
      Meteojob:           toArray(data.Meteojob),
      APEC:               toArray(data.APEC),
      HelloWork:          toArray(data.HelloWork),
      "France Travail":   toArray(data["France Travail"]),
      Greenhouse:         toArray(data.Greenhouse),
      Lever:              toArray(data.Lever),
      WTTJ:               toArray(data.WTTJ || data["Welcome to the Jungle"]),
      SmartRecruiters:    toArray(data.SmartRecruiters),
    };
  };

  const searchPayload = React.useCallback(() => ({
    keyword,
    city,
    greenhouse_boards: boardsConfig.greenhouse_boards,
    lever_boards: boardsConfig.lever_boards,
    smartrecruiters_companies: boardsConfig.smartrecruiters_companies,
  }), [keyword, city, boardsConfig]);

  const hasConfiguredBoards = (platform) => {
    if (platform === "Greenhouse") return boardsConfig.greenhouse_boards.length > 0;
    if (platform === "Lever") return boardsConfig.lever_boards.length > 0;
    if (platform === "SmartRecruiters") return boardsConfig.smartrecruiters_companies.length > 0;
    return true;
  };

  const handleBoardsSave = async (config) => {
    saveBoardsConfig(config);
    setBoardsConfig(config);

    await Promise.all([
      fetch(`${API_BASE_URL}/boards-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          greenhouse_boards: config.greenhouse_boards,
          lever_boards: config.lever_boards,
        }),
      }),
      fetch(`${API_BASE_URL}/smartrecruiters-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companies: config.smartrecruiters_companies,
        }),
      }),
    ]);
  };


  const fetchAutoResults = React.useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auto-results`);
      if (!res.ok) return;
      const data = await res.json();
      setJobs(normalizeJobs(data));
    } catch (err) {
      console.warn("[Auto] Erreur :", err.message);
    }
  }, []);


  const fetchSchedulerStatus = React.useCallback(async () => {
    try {
      const res  = await fetch(`${API_BASE_URL}/scheduler-status`);
      const data = await res.json();
      const autoRunning = data.auto_running;
      if (prevAutoRunning.current === true && autoRunning === false) {
        fetchAutoResults();
      }
      prevAutoRunning.current = autoRunning;
      setSchedulerStatus({
        nextRunTime:   data.next_run_time ? new Date(data.next_run_time) : null,
        countdown:     data.countdown,
        autoRunning,
        manualEnabled: data.manual_enabled,
      });
    } catch (err) {
      console.error("Erreur scheduler status", err);
    }
  }, [fetchAutoResults]);


  React.useEffect(() => {
    fetchSchedulerStatus();
    fetchAutoResults();
    const id = setInterval(fetchSchedulerStatus, 10000);
    return () => clearInterval(id);
  }, [fetchSchedulerStatus, fetchAutoResults]);

  React.useEffect(() => {
    if (!schedulerStatus.nextRunTime) return;
    const id = setInterval(() => {
      setSchedulerStatus((prev) => {
        if (!prev.nextRunTime) return prev;
        const countdown = Math.max(0, Math.floor((new Date(prev.nextRunTime) - new Date()) / 1000));
        return { ...prev, countdown, manualEnabled: !prev.autoRunning && countdown > 0 };
      });
    }, 1000);
    return () => clearInterval(id);
  }, [schedulerStatus.nextRunTime]);


  const findApplication = (job) =>
    applications.find(
      (app) =>
        app.title   === job.title &&
        app.company === job.company &&
        ["En cours", "Accepté", "Refusé"].includes(app.status)
    );

  const handleApply = (job) => {
    const existing = findApplication(job);
    if (existing) { alert("Vous avez déjà postulé à cette offre."); return; }
    const alreadyApplied = window.confirm("Avez-vous déjà postulé ?\n\nOK = Oui\nAnnuler = Non");
    if (!alreadyApplied) { if (job.url) window.open(job.url, "_blank"); return; }
    setApplications((prev) => [
      ...prev,
      {
        id:             Date.now(),
        ...job,
        status:         "En cours",
        appliedDate:    new Date().toISOString(),
        followUpDate:   addBusinessDays(new Date(), 10).toISOString(),
        reminderActive: true,
      },
    ]);
    alert("Candidature ajoutée !");
    setSelectedJob(null);
  };

  const fetchAll = async () => {
    if (!schedulerStatus.manualEnabled) return;
    setLoading(true);
    try {
      const res  = await fetch(`${API_BASE_URL}/search-all`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(searchPayload()),
      });
      const data = await res.json();
      setJobs(normalizeJobs(data));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlatform = async (platform) => {
    if (!schedulerStatus.manualEnabled) return;
    setLoading(true);
    try {
      const res  = await fetch(`${API_BASE_URL}/search/${platform}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(searchPayload()),
      });
      const data = await res.json();
      setJobs((prev) => ({ ...prev, [platform]: data.jobs || [] }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = (list) => {
    const blocked = blockedCompanies.map((c) => c.toLowerCase().trim()).filter(Boolean);
    const visible = list.filter((j) => {
      const co = (j.company || "").toLowerCase().trim();
      return !co || !blocked.some((b) => co.includes(b));
    });
    if (filterType === "offre")     return visible.filter((j) => j.type !== "spontanee");
    if (filterType === "spontanee") return visible.filter((j) => j.type === "spontanee");
    return visible;
  };

  const total = Object.values(jobs).reduce((s, l) => s + l.length, 0);

  return (
    <div className="min-h-screen bg-slate-100 p-6">

      <h1 className="text-4xl font-bold text-center mb-1">Job Scraper Dashboard</h1>

      {total > 0 && (
        <p className="text-center text-gray-500 mb-4">
          {total} offre{total > 1 ? "s" : ""} trouvée{total > 1 ? "s" : ""}
        </p>
      )}

      <div className="flex justify-center gap-3 mb-6 flex-wrap">
        <button onClick={() => navigate("/cover-letter")}
          className="bg-indigo-600 text-white px-5 py-2 rounded-xl hover:bg-indigo-700 text-sm">
          Cover Letter
        </button>
        <button onClick={() => navigate("/applications")}
          className="bg-emerald-600 text-white px-5 py-2 rounded-xl hover:bg-emerald-700 text-sm">
          Applications
        </button>
        <button onClick={() => navigate("/blocked-companies")}
          className="bg-red-600 text-white px-5 py-2 rounded-xl hover:bg-red-700 text-sm">
          Gérer les blocs ({blockedCompanies.length})
        </button>
        <button onClick={() => navigate("/notifications")}
          className="bg-violet-600 text-white px-5 py-2 rounded-xl hover:bg-violet-700 text-sm">
          Notifications
        </button>
        <button
          onClick={() => setShowBoardsModal(true)}
          className="bg-slate-700 text-white px-5 py-2 rounded-xl hover:bg-slate-800 text-sm flex items-center gap-1.5"
        >
          ⚙️ Boards / entreprises
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow p-4 mb-4 flex gap-3 flex-wrap items-center">
        <input
          className="border rounded-xl p-3 flex-1 min-w-[160px] text-sm"
          placeholder="Développeur alternance"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchAll()}
        />
        <input
          className="border rounded-xl p-3 flex-1 min-w-[140px] text-sm"
          placeholder="Montpellier"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchAll()}
        />
        <button
          onClick={fetchAll}
          disabled={!schedulerStatus.manualEnabled || loading}
          className={`px-6 py-3 rounded-xl font-semibold text-sm ${
            schedulerStatus.manualEnabled && !loading
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : "bg-slate-300 text-slate-600 cursor-not-allowed"
          }`}
        >
          Rechercher tout
        </button>
      </div>

      <div className="text-center mb-4 text-sm text-gray-600">
        {schedulerStatus.autoRunning ? (
          <span className="font-semibold text-blue-700 animate-pulse">
            ⏳ Recherche automatique en cours — les résultats s'afficheront automatiquement
          </span>
        ) : schedulerStatus.manualEnabled ? (
          <span>
            Prochaine recherche automatique dans{" "}
            <span className="font-semibold">{formatCountdown(schedulerStatus.countdown)}</span>
          </span>
        ) : (
          <span className="font-semibold text-orange-700">
            Recherche automatique imminente — recherches manuelles désactivées
          </span>
        )}
      </div>

      {jobs["Bonne Alternance"].length > 0 && (
        <div className="flex justify-center gap-2 mb-4">
          {["tout", "offre", "spontanee"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
                filterType === t ? "bg-blue-600 text-white" : "bg-white text-gray-600 border hover:bg-slate-50"
              }`}
            >
              {t === "tout" && "Tout"}
              {t === "offre" && "Offres d'emploi"}
              {t === "spontanee" && "Candidatures spontanées"}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="text-center mb-4 text-blue-600 font-bold animate-pulse">
          Recherche en cours...
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-5">
        {Object.entries(jobs).map(([platform, platformJobs]) => {
          const visible     = filtered(platformJobs);
          const appliedList = visible.filter((j) =>  findApplication(j));
          const notApplied  = visible.filter((j) => !findApplication(j));

          const isExternal = platform === "Greenhouse" || platform === "Lever" || platform === "SmartRecruiters";

          return (
            <div key={platform} className="bg-white rounded-2xl shadow p-4 flex flex-col">

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5">
                  {platform === "Greenhouse" && <span className="text-base">🟢</span>}
                  {platform === "Lever"      && <span className="text-base">🟣</span>}
                  {platform === "SmartRecruiters" && <span className="text-base">SR</span>}
                  <h2 className="text-base font-bold">{platform}</h2>
                </div>
                {platformJobs.length > 0 && (
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                    {visible.length}/{platformJobs.length}
                  </span>
                )}
              </div>

              <button
                onClick={() => {
                  if (isExternal) {
                    setShowBoardsModal(true);
                  } else {
                    fetchPlatform(platform);
                  }
                }}
                className={`w-full mb-3 py-2 rounded-xl text-sm ${
                  schedulerStatus.manualEnabled && !loading
                    ? platform === "Greenhouse"
                      ? "bg-green-600 hover:bg-green-700 text-white"
                      : platform === "Lever"
                        ? "bg-violet-600 hover:bg-violet-700 text-white"
                        : platform === "SmartRecruiters"
                          ? "bg-sky-600 hover:bg-sky-700 text-white"
                          : "bg-purple-600 hover:bg-purple-700 text-white"
                    : "bg-slate-300 text-slate-600 cursor-not-allowed"
                }`}
                disabled={!schedulerStatus.manualEnabled || loading}
              >
                {isExternal
                  ? `⚙️ Configurer ${platform}`
                  : `Rechercher ${platform}`}
              </button>

              {isExternal && (
                <button
                  onClick={() => fetchPlatform(platform)}
                  className={`w-full mb-3 py-2 rounded-xl text-sm ${
                    schedulerStatus.manualEnabled && !loading && hasConfiguredBoards(platform)
                      ? platform === "Greenhouse"
                        ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                        : platform === "Lever"
                          ? "bg-purple-600 hover:bg-purple-700 text-white"
                          : "bg-sky-600 hover:bg-sky-700 text-white"
                      : "bg-slate-300 text-slate-600 cursor-not-allowed"
                  }`}
                  disabled={!schedulerStatus.manualEnabled || loading || !hasConfiguredBoards(platform)}
                >
                  {`Rechercher manuellement ${platform}`}
                </button>
              )}

              {platform === "Bonne Alternance" && platformJobs.length > 0 && (
                <div className="text-xs text-gray-400 mb-2 flex gap-2 flex-wrap">
                  <span>📋 {platformJobs.filter((j) => j.type !== "spontanee").length} offres</span>
                  <span>🏢 {platformJobs.filter((j) => j.type === "spontanee").length} spontanées</span>
                </div>
              )}

              {platformJobs.filter((j) => j.is_new).length > 0 && (
                <div className="text-xs font-semibold text-emerald-600 mb-2">
                  ✨ {platformJobs.filter((j) => j.is_new).length} nouvelle
                  {platformJobs.filter((j) => j.is_new).length > 1 ? "s" : ""} offre
                  {platformJobs.filter((j) => j.is_new).length > 1 ? "s" : ""}
                </div>
              )}

              <div className="space-y-2 overflow-y-auto flex-1" style={{ maxHeight: "60vh" }}>
                {visible.length === 0 ? (
                  <p className="text-gray-400 text-center text-sm py-4">
                    {isExternal && platformJobs.length === 0 && !hasConfiguredBoards(platform)
                      ? "Aucun board configuré — cliquez sur le bouton ci-dessus"
                      : platformJobs.length > 0
                        ? "Filtre actif — aucun résultat"
                        : schedulerStatus.autoRunning
                          ? "⏳ Recherche en cours..."
                          : "aucune offre"}
                  </p>
                ) : (
                  <>
                    {notApplied.map((job, i) => (
                      <JobCard
                        key={job.url || `na-${i}`}
                        job={job}
                        existing={findApplication(job)}
                        onClick={() => setSelectedJob(job)}
                      />
                    ))}
                    {appliedList.length > 0 && (
                      <div className="text-sm font-semibold text-gray-700 pt-2 border-t">
                        Offres déjà postulées
                      </div>
                    )}
                    {appliedList.map((job, i) => (
                      <JobCard
                        key={job.url || `ap-${i}`}
                        job={job}
                        existing={findApplication(job)}
                        onClick={() => setSelectedJob(job)}
                      />
                    ))}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {selectedJob && (
        <JobModal
          job={selectedJob}
          existing={findApplication(selectedJob)}
          getTimeAgo={getTimeAgo}
          onApply={handleApply}
          onClose={() => setSelectedJob(null)}
        />
      )}

      {showBoardsModal && (
        <BoardsConfigModal
          initialConfig={boardsConfig}
          onSave={handleBoardsSave}
          onClose={() => setShowBoardsModal(false)}
        />
      )}
    </div>
  );
}
