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

      <h1 className="text-4xl font-bold text-center mb-10">
        Dashboard des Candidatures
      </h1>

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
                className="bg-white rounded-2xl shadow p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
              >
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