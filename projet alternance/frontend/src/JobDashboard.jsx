import React from "react";
import { useNavigate } from "react-router-dom";

const SOURCE_COLORS = {
  offres_emploi_lba:        "bg-blue-100 text-blue-700",
  recruteur_lba:            "bg-emerald-100 text-emerald-700",
  "France Travail":        "bg-orange-100 text-orange-700",
  HelloWork:                "bg-cyan-100 text-cyan-700",
  PASS:                     "bg-purple-100 text-purple-700",
  default:                  "bg-gray-100 text-gray-600",
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
function JobCard({ job, existing, getTimeAgo, onClick }) {
  return (
    <div
      onClick={onClick}
      className={"p-3 border rounded-xl cursor-pointer hover:bg-slate-50 transition space-y-1" + (job.is_new ? " border-l-4 border-l-emerald-400" : "")}
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

      {job.company && (
        <p className="text-sm text-gray-600">{job.company}</p>
      )}

      <p className="text-xs text-gray-400">{job.location}</p>

      {/* Contrat + remote */}
      {(job.contract?.length > 0 || job.remote) && (
        <p className="text-xs text-indigo-500">
          {job.contract?.join(", ")}
          {job.remote && job.remote !== "onsite"
            ? ` · ${job.remote === "remote" ? "Télétravail" : "Hybride"}`
            : ""}
        </p>
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

        {job.company && (
          <p className="text-lg font-medium text-gray-700">{job.company}</p>
        )}
        <p className="text-gray-400 text-sm mb-1">{job.location}</p>

        {(job.contract?.length > 0 || job.remote) && (
          <p className="text-sm text-indigo-600 mb-1">
            {job.contract?.join(", ")}
            {job.remote && job.remote !== "onsite"
              ? ` · ${job.remote === "remote" ? "Télétravail" : "Hybride"}`
              : ""}
          </p>
        )}

        {job.type === "spontanee" && (
          <div className="bg-emerald-50 rounded-xl p-3 mb-3 text-sm space-y-1">
            {job.size    && <p>👥 <span className="text-gray-600">{job.size} salariés</span></p>}
            {job.opco    && <p>🏦 <span className="text-gray-600">OPCO : {job.opco}</span></p>}
            {job.website && (
              <p>🌐 <a href={job.website} target="_blank" rel="noreferrer"
                className="text-blue-600 underline">{job.website}</a></p>
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
            <a
              href={`tel:${job.phone}`}
              className="bg-blue-600 text-white px-5 py-2 rounded-xl hover:bg-blue-700"
            >
              Appeler
            </a>
          )}

          <button
            onClick={onClose}
            className="bg-red-500 text-white px-5 py-2 rounded-xl hover:bg-red-600"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Dashboard principal ──────────────────────────────────────
export default function JobDashboard({ applications, setApplications, blockedCompanies, setBlockedCompanies }) {
  const navigate = useNavigate();

  const [jobs, setJobs] = React.useState({
    LinkedIn:          [],
    Indeed:            [],
    "Bonne Alternance": [],
    Meteojob:          [],
    APEC:              [],
    HelloWork:         [],
    "France Travail": [],
  });

  const [selectedJob, setSelectedJob] = React.useState(null);
  const [keyword,     setKeyword]     = React.useState("");
  const [city,        setCity]        = React.useState("");
  const [loading,     setLoading]     = React.useState(false);
  const [schedulerStatus, setSchedulerStatus] = React.useState({
    nextRunTime: null,
    countdown: null,
    autoRunning: false,
    manualEnabled: true,
  });

  const [filterType, setFilterType] = React.useState("tout");

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
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const fetchSchedulerStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/scheduler-status");
      const data = await res.json();
      setSchedulerStatus({
        nextRunTime: data.next_run_time ? new Date(data.next_run_time) : null,
        countdown: data.countdown,
        autoRunning: data.auto_running,
        manualEnabled: data.manual_enabled,
      });
    } catch (err) {
      console.error("Erreur scheduler status", err);
    }
  };

  const getTimeAgo = (dateString) => {
    const diffDays = Math.floor(
      (new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24)
    );
    if (diffDays < 30) return `${diffDays} jour${diffDays > 1 ? "s" : ""}`;
    return `${Math.floor(diffDays / 30)} mois`;
  };

  React.useEffect(() => {
    fetchSchedulerStatus();
    const intervalId = setInterval(fetchSchedulerStatus, 30000);
    return () => clearInterval(intervalId);
  }, []);

  React.useEffect(() => {
    if (!schedulerStatus.nextRunTime) return;
    const timerId = setInterval(() => {
      setSchedulerStatus((prev) => {
        if (!prev.nextRunTime) return prev;
        const countdown = Math.max(0, Math.floor((new Date(prev.nextRunTime) - new Date()) / 1000));
        return {
          ...prev,
          countdown,
          manualEnabled: !prev.autoRunning && countdown > 0,
        };
      });
    }, 1000);
    return () => clearInterval(timerId);
  }, [schedulerStatus.nextRunTime]);

  const findApplication = (job) =>
    applications.find(
      (app) =>
        app.title === job.title &&
        app.company === job.company &&
        ["En cours", "Accepté", "Refusé"].includes(app.status)
    );
  const handleApply = (job) => {
    const existing = findApplication(job);
    if (existing) { alert("Vous avez déjà postulé à cette offre."); return; }

    const alreadyApplied = window.confirm(
      "Avez-vous déjà postulé ?\n\nOK = Oui\nAnnuler = Non"
    );

    if (!alreadyApplied) {
      if (job.url) window.open(job.url, "_blank");
      return;
    }

    setApplications((prev) => [
      ...prev,
      {
        id: Date.now(),
        ...job,
        status:          "En cours",
        appliedDate:     new Date().toISOString(),
        followUpDate:    addBusinessDays(new Date(), 10).toISOString(),
        reminderActive:  true,
      },
    ]);

    alert("Candidature ajoutée !");
    setSelectedJob(null);
  };
  const fetchAll = async () => {
    if (!schedulerStatus.manualEnabled) return;
    setLoading(true);
    try {
      const res  = await fetch("http://localhost:8000/search-all", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ keyword, city }),
      });
      const data = await res.json();
      setJobs({
        LinkedIn:          data.LinkedIn         || [],
        Indeed:            data.Indeed           || [],
        "Bonne Alternance": data["Bonne Alternance"] || [],
        Meteojob:          data.Meteojob         || [],
        APEC:              data.APEC             || [],
        HelloWork:         data.HelloWork        || [],
        "France Travail": data["France Travail"] || [],
      });
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
      const res  = await fetch(`http://localhost:8000/search/${platform}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ keyword, city }),
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
    const normalizedBlocked = blockedCompanies.map((company) => company.toLowerCase().trim()).filter(Boolean);
    const visible = list.filter((j) => {
      const company = (j.company || "").toLowerCase().trim();
      if (!company) return true;
      return !normalizedBlocked.some((blocked) => company.includes(blocked));
    });

    if (filterType === "tout") return visible;
    if (filterType === "offre") return visible.filter((j) => j.type !== "spontanee");
    if (filterType === "spontanee") return visible.filter((j) => j.type === "spontanee");
    return visible;
  };

  const total = Object.values(jobs).reduce((s, l) => s + l.length, 0);

  return (
    <div className="min-h-screen bg-slate-100 p-6">

      <h1 className="text-4xl font-bold text-center mb-1">
        Job Scraper Dashboard
      </h1>
      {total > 0 && (
        <p className="text-center text-gray-500 mb-4">
          {total} offre{total > 1 ? "s" : ""} trouvée{total > 1 ? "s" : ""}
        </p>
      )}
      <div className="flex justify-center gap-4 mb-6 flex-wrap">
        <button
          onClick={() => navigate("/cover-letter")}
          className="bg-indigo-600 text-white px-5 py-2 rounded-xl hover:bg-indigo-700"
        >
          Cover Letter
        </button>
        <button
          onClick={() => navigate("/applications")}
          className="bg-emerald-600 text-white px-5 py-2 rounded-xl hover:bg-emerald-700"
        >
          Applications
        </button>
        <button
          onClick={() => navigate("/cover-letter")}
          className="bg-indigo-600 text-white px-5 py-2 rounded-xl hover:bg-indigo-700"
        >
          Cover Letter
        </button>
        <button
          onClick={() => navigate("/applications")}
          className="bg-emerald-600 text-white px-5 py-2 rounded-xl hover:bg-emerald-700"
        >
          Applications
        </button>
        <button
          onClick={() => navigate("/blocked-companies")}
          className="bg-red-600 text-white px-5 py-2 rounded-xl hover:bg-red-700"
        >
          Gérer les blocs ({blockedCompanies.length})
        </button>
        <button
          onClick={() => navigate("/notifications")}
          className="bg-violet-600 text-white px-5 py-2 rounded-xl hover:bg-violet-700"
        >
          Notifications
        </button>
      </div>
      <div className="bg-white rounded-2xl shadow p-4 mb-4 flex gap-3 flex-wrap items-center">
        <input
          className="border rounded-xl p-3 flex-1 min-w-[160px]"
          placeholder="Développeur alternance"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchAll()}
        />
        <input
          className="border rounded-xl p-3 flex-1 min-w-[140px]"
          placeholder="Montpellier"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchAll()}
        />
        <button
          onClick={fetchAll}
          className={`px-6 py-3 rounded-xl font-semibold ${schedulerStatus.manualEnabled && !loading ? "bg-blue-600 hover:bg-blue-700 text-white" : "bg-slate-300 text-slate-600 cursor-not-allowed"}`}
          disabled={!schedulerStatus.manualEnabled || loading}
        >
          Rechercher tout
        </button>
      </div>
      <div className="text-center mb-4 text-sm text-gray-600">
        {schedulerStatus.autoRunning ? (
          <span className="font-semibold text-blue-700">
            Recherche automatique en cours — recherches manuelles désactivées
          </span>
        ) : schedulerStatus.manualEnabled ? (
          <span>
            Prochaine recherche automatique dans <span className="font-semibold">{formatCountdown(schedulerStatus.countdown)}</span>
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
                filterType === t
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 border hover:bg-slate-50"
              }`}
            >
              {t === "tout"      && "Tout"}
              {t === "offre"     && "Offres d'emploi"}
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Object.entries(jobs).map(([platform, platformJobs]) => {
          const visible = filtered(platformJobs);
          const appliedList = visible.filter((j) => findApplication(j));
          const notAppliedList = visible.filter((j) => !findApplication(j));

          return (
            <div key={platform} className="bg-white rounded-2xl shadow p-4 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold">{platform}</h2>
                {platformJobs.length > 0 && (
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                    {visible.length}/{platformJobs.length}
                  </span>
                )}
              </div>

              <button
                onClick={() => fetchPlatform(platform)}
                className={`w-full mb-3 py-2 rounded-xl text-sm ${schedulerStatus.manualEnabled && !loading ? "bg-purple-600 hover:bg-purple-700 text-white" : "bg-slate-300 text-slate-600 cursor-not-allowed"}`}
                disabled={!schedulerStatus.manualEnabled || loading}
              >
                Rechercher {platform}
              </button>

              {/* stats LBA */}
              {platform === "Bonne Alternance" && platformJobs.length > 0 && (
                <div className="text-xs text-gray-400 mb-2 flex gap-2 flex-wrap">
                  <span>📋 {platformJobs.filter(j => j.type !== "spontanee").length} offres</span>
                  <span>🏢 {platformJobs.filter(j => j.type === "spontanee").length} spontanées</span>
                </div>
              )}
              {platformJobs.filter(j => j.is_new).length > 0 && (
                <div className="text-xs font-semibold text-emerald-600 mb-2">
                  ✨ {platformJobs.filter(j => j.is_new).length} nouvelle{platformJobs.filter(j => j.is_new).length > 1 ? "s" : ""} offre{platformJobs.filter(j => j.is_new).length > 1 ? "s" : ""}
                </div>
              )}

              <div className="space-y-2 overflow-y-auto flex-1" style={{ maxHeight: "60vh" }}>
                {visible.length === 0 ? (
                  <p className="text-gray-400 text-center text-sm py-4">
                    {platformJobs.length > 0 ? "Filtre actif — aucun résultat" : "aucune offre"}
                  </p>
                ) : (
                  <>
                    {notAppliedList.map((job, index) => (
                      <JobCard
                        key={job.url || `na-${index}`}
                        job={job}
                        existing={findApplication(job)}
                        getTimeAgo={getTimeAgo}
                        onClick={() => setSelectedJob(job)}
                      />
                    ))}

                    {appliedList.length > 0 && (
                      <div className="text-lg font-semibold text-gray-800 pt-2">
                        Offres déjà postulées
                      </div>
                    )}

                    {appliedList.map((job, index) => (
                      <JobCard
                        key={job.url || `ap-${index}`}
                        job={job}
                        existing={findApplication(job)}
                        getTimeAgo={getTimeAgo}
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
    </div>
  );
}