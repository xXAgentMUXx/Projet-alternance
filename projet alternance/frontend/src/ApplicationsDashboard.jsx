import React from "react";
import { useNavigate } from "react-router-dom";

export default function ApplicationsDashboard({
  applications,
  setApplications
}) {
  const navigate = useNavigate();

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
  const resetReminder = (id) => {
    setApplications((prev) =>
      prev.map((app) =>
        app.id === id
          ? {
              ...app,
              followUpDate: addBusinessDays(
                new Date(),
                10
              ).toISOString(),
              reminderActive: true
            }
          : app
      )
    );
  };

  const updateStatus = (
    id,
    newStatus
  ) => {
    setApplications((prev) =>
      prev.map((app) =>
        app.id === id
          ? {
              ...app,
              status: newStatus,
              reminderActive:
                newStatus ===
                "En cours"
            }
          : app
      )
    );
  };

  const deleteApplication = (id) => {
    if (!window.confirm("Supprimer cette candidature ?")) {
      return;
    }
    setApplications((prev) => prev.filter((app) => app.id !== id));
  };

  const statusColor = {
    "En cours":
      "bg-yellow-100 text-yellow-700",

    "Accepté":
      "bg-green-100 text-green-700",

    "Refusé":
      "bg-red-100 text-red-700"
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">

      <div className="relative mb-10">
        <button
          onClick={() => navigate(-1)}
          className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline"
        >
          ← Retour
        </button>
        <h1 className="text-4xl font-bold text-center">
          Dashboard des Candidatures
        </h1>
      </div>

      {applications.length === 0 ? (
        <p className="text-center text-gray-500">
          Aucune candidature enregistrée
        </p>
      ) : (
        <div className="grid gap-5 max-w-5xl mx-auto">

          {applications.map((app) => {
            let daysLeft = null;

            if (
              app.reminderActive &&
              app.followUpDate
            ) {
              daysLeft = Math.ceil(
                (
                  new Date(
                    app.followUpDate
                  ) - new Date()
                ) /
                  (1000 *
                    60 *
                    60 *
                    24)
              );
            }

            return (
              <div
                key={app.id}
                className="bg-white rounded-2xl shadow p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 relative"
              >
                <button
                  onClick={() => deleteApplication(app.id)}
                  className="absolute right-4 top-4 text-gray-400 hover:text-red-600 rounded-full p-2"
                  aria-label="Supprimer candidature"
                >
                  ×
                </button>
                <div>
                  <h2 className="text-2xl font-bold">
                    {app.title}
                  </h2>

                  <p className="text-lg text-gray-700">
                    {app.company}
                  </p>

                  <p className="text-sm text-gray-500">
                    Postulé le :{" "}
                    {new Date(
                      app.appliedDate
                    ).toLocaleDateString()}
                  </p>

                  {app.reminderActive && (
                    <p className="mt-2 text-blue-600 font-semibold">
                      Relance dans :{" "}
                      {daysLeft} jour
                      {daysLeft > 1
                        ? "s"
                        : ""}
                    </p>
                  )}
                </div>

                <div className="flex flex-col items-start md:items-end gap-3">

                  <span
                    className={`px-4 py-2 rounded-xl font-semibold ${statusColor[app.status]}`}
                  >
                    {app.status}
                  </span>

                  <select
                    value={app.status}
                    onChange={(e) =>
                      updateStatus(
                        app.id,
                        e.target.value
                      )
                    }
                    className="border rounded-xl p-2"
                  >
                    <option>
                      En cours
                    </option>
                    <option>
                      Accepté
                    </option>
                    <option>
                      Refusé
                    </option>
                  </select>

                  {app.status ===
                    "En cours" && (
                    <>
                      <button
                        onClick={() =>
                          resetReminder(
                            app.id
                          )
                        }
                        className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700"
                      >
                        Relance faite
                      </button>

                      <button
                        onClick={() =>
                          navigate(
                            `/networking/${app.id}`
                          )
                        }
                        className="bg-purple-600 text-white px-4 py-2 rounded-xl hover:bg-purple-700"
                      >
                        Gestion / Relance
                      </button>
                    </>
                  )}

                </div>
              </div>
            );
          })}

        </div>
      )}
    </div>
  );
}