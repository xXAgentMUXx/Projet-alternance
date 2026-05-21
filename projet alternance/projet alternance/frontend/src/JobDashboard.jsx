import React from "react";
import { useNavigate } from "react-router-dom";

export default function JobDashboard({
  applications,
  setApplications
}) {
  const navigate = useNavigate();

  const [jobs, setJobs] = React.useState({
    LinkedIn: [],
    Indeed: [],
    "Bonne Alternance": [],
    Meteojob: []
  });

  const [selectedJob, setSelectedJob] = React.useState(null);
  const [keyword, setKeyword] = React.useState("");
  const [city, setCity] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  // -------------------------
  // ajoute 10 jours ouvrés
  // -------------------------
  const addBusinessDays = (date, days) => {
    let result = new Date(date);
    let added = 0;

    while (added < days) {
      result.setDate(result.getDate() + 1);

      const day = result.getDay();

      if (day !== 0 && day !== 6) {
        added++;
      }
    }

    return result;
  };

  // -------------------------
  // combien de temps depuis la candidature
  // -------------------------
  const getTimeAgo = (dateString) => {
    const now = new Date();
    const past = new Date(dateString);

    const diffDays = Math.floor(
      (now - past) / (1000 * 60 * 60 * 24)
    );

    if (diffDays < 30) {
      return `${diffDays} jour${diffDays > 1 ? "s" : ""}`;
    }

    const months = Math.floor(diffDays / 30);

    return `${months} mois`;
  };

  // -------------------------
  // vérifier si déjà candidaté
  // -------------------------
  const findApplication = (job) => {
    return applications.find(
      (app) =>
        app.title === job.title &&
        app.company === job.company
    );
  };

  // -------------------------
  // clic postuler
  // -------------------------
  const handleApply = (job) => {
    const existing = findApplication(job);

    if (existing) {
      alert("Vous avez déjà postulé à cette offre.");
      return;
    }

    const alreadyApplied = window.confirm(
      "Avez-vous déjà postulé ?\n\nOK = Oui\nAnnuler = Non"
    );

    if (!alreadyApplied) {
      window.open(job.url, "_blank");
      return;
    }

    const newApplication = {
      id: Date.now(),
      ...job,
      status: "En cours",
      appliedDate: new Date().toISOString(),
      followUpDate: addBusinessDays(
        new Date(),
        10
      ).toISOString(),
      reminderActive: true
    };

    setApplications((prev) => [
      ...prev,
      newApplication
    ]);

    alert("Candidature ajoutée !");
    setSelectedJob(null);
  };

  // -------------------------
  // recherche globale
  // -------------------------
  const handleSearchAll = async () => {
    try {
      setLoading(true);

      const res = await fetch(
        "http://localhost:8000/search-all",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            keyword,
            city
          })
        }
      );

      const data = await res.json();

      setJobs({
        LinkedIn: data.LinkedIn || [],
        Indeed: data.Indeed || [],
        "Bonne Alternance":
          data["Bonne Alternance"] || [],
        Meteojob: data.Meteojob || []
      });

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // recherche plateforme
  // -------------------------
  const handlePlatformSearch = async (
    platform
  ) => {
    try {
      setLoading(true);

      const res = await fetch(
        `http://localhost:8000/search/${platform}`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            keyword,
            city
          })
        }
      );

      const data = await res.json();

      setJobs((prev) => ({
        ...prev,
        [platform]: data.jobs || []
      }));

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">

      <h1 className="text-4xl font-bold text-center mb-4">
        Job Scraper Dashboard
      </h1>

      {/* navigation */}
      <div className="flex justify-center gap-4 mb-8">
        <button
          onClick={() =>
            navigate("/cover-letter")
          }
          className="bg-indigo-600 text-white px-5 py-2 rounded-xl hover:bg-indigo-700"
        >
          Cover Letter
        </button>

        <button
          onClick={() =>
            navigate("/applications")
          }
          className="bg-emerald-600 text-white px-5 py-2 rounded-xl hover:bg-emerald-700"
        >
          Applications
        </button>
      </div>

      {/* recherche */}
      <div className="bg-white rounded-2xl shadow p-6 mb-8 flex gap-4 flex-wrap">
        <input
          className="border rounded-xl p-3 flex-1"
          placeholder="Développeur alternance"
          value={keyword}
          onChange={(e) =>
            setKeyword(e.target.value)
          }
        />

        <input
          className="border rounded-xl p-3 flex-1"
          placeholder="Montpellier"
          value={city}
          onChange={(e) =>
            setCity(e.target.value)
          }
        />

        <button
          onClick={handleSearchAll}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700"
        >
          Rechercher tout
        </button>
      </div>

      {loading && (
        <div className="text-center mb-6 text-blue-600 font-bold">
          Recherche en cours...
        </div>
      )}

      {/* colonnes */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Object.entries(jobs).map(
          ([platform, platformJobs]) => (
            <div
              key={platform}
              className="bg-white rounded-2xl shadow p-4"
            >
              <h2 className="text-xl font-bold mb-4 text-center">
                {platform}
              </h2>

              <button
                onClick={() =>
                  handlePlatformSearch(
                    platform
                  )
                }
                className="w-full mb-4 bg-purple-600 text-white py-2 rounded-xl hover:bg-purple-700"
              >
                Rechercher {platform}
              </button>

              <div className="space-y-3">
                {platformJobs.length === 0 ? (
                  <p className="text-gray-400 text-center">
                    aucune offre
                  </p>
                ) : (
                  platformJobs.map(
                    (job, index) => {
                      const existing =
                        findApplication(job);

                      return (
                        <div
                          key={
                            job.id || index
                          }
                          onClick={() =>
                            setSelectedJob(
                              job
                            )
                          }
                          className="p-3 border rounded-xl cursor-pointer hover:bg-slate-50"
                        >
                          <h3 className="font-semibold">
                            {job.title}
                          </h3>

                          <p className="text-sm text-gray-600">
                            {job.company}
                          </p>

                          <p className="text-sm text-gray-500">
                            {job.location}
                          </p>

                          {existing && (
                            <p className="text-xs text-green-600 font-semibold mt-2">
                              Candidature faite il y a{" "}
                              {getTimeAgo(
                                existing.appliedDate
                              )}
                            </p>
                          )}
                        </div>
                      );
                    }
                  )
                )}
              </div>
            </div>
          )
        )}
      </div>

      {/* popup */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-lg w-full">

            <h2 className="text-2xl font-bold mb-2">
              {selectedJob.title}
            </h2>

            <p className="text-lg">
              {selectedJob.company}
            </p>

            <p className="text-gray-500 mb-4">
              {selectedJob.location}
            </p>

            <p className="mb-6">
              {selectedJob.description ||
                "Pas de description"}
            </p>

            <div className="flex gap-3">
              <button
                onClick={() =>
                  handleApply(
                    selectedJob
                  )
                }
                className="bg-green-600 text-white px-5 py-2 rounded-xl hover:bg-green-700"
              >
                Postuler
              </button>

              <button
                onClick={() =>
                  setSelectedJob(null)
                }
                className="bg-red-500 text-white px-5 py-2 rounded-xl hover:bg-red-600"
              >
                Fermer
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}