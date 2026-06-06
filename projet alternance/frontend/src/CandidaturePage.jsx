import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function CandidaturePage() {

  const location = useLocation();
  const navigate = useNavigate();

  const person = location.state?.person || {};
  const initialStatus = location.state?.status || null;
  const savedCompany = location.state?.company || person.current_company || person.company || "";

  const [companyDescription, setCompanyDescription] = React.useState("");
  const [jobDescription, setJobDescription] = React.useState("");

  const [generatedMessage, setGeneratedMessage] =
    React.useState("");

  const [loading, setLoading] =
    React.useState(false);
  const [inviteStatus, setInviteStatus] = React.useState(initialStatus);

  React.useEffect(() => {
    // try to read status from localStorage if not provided (for the same saved company)
    if (!inviteStatus) {
      try {
        const raw = localStorage.getItem("addedPeople");
        if (raw) {
          const arr = JSON.parse(raw);
          const found = arr.find(
            (p) => (p.profile_link === person.profile_link || p.id === person.id) && p.savedForCompany === savedCompany
          );
          if (found && found.status) setInviteStatus(found.status);
        }
      } catch (e) {}
    }
  }, [inviteStatus, person]);

  const handleCreateMessage = async () => {
    try {
      setLoading(true);

      const payload = {
        contact_name: person.name || "",
        company_name: person.current_company || person.company || "",
        headline: person.headline || "",
        company_description: companyDescription,
        job_description: jobDescription,
      };

      const response = await fetch("http://localhost:8000/generate-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      setGeneratedMessage(data.message || "");
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la génération");
    } finally {
      setLoading(false);
    }
  };

  const _saveStatusToStorage = (status) => {
    try {
      const raw = localStorage.getItem("addedPeople");
      const arr = raw ? JSON.parse(raw) : [];
      let found = false;
      const next = arr.map((p) => {
        if ((p.profile_link === person.profile_link || p.id === person.id) && p.savedForCompany === savedCompany) {
          found = true;
          return { ...p, status };
        }
        return p;
      });

      if (!found) {
        // add a new saved entry for this company
        next.push({ ...person, status, savedForCompany: savedCompany });
      }
      localStorage.setItem("addedPeople", JSON.stringify(next));
    } catch (e) {}
  };

  const markInvited = () => {
    setInviteStatus("invited");
    _saveStatusToStorage("invited");
    alert("Statut mis à jour : invitée");
  };

  const markNotInvited = () => {
    setInviteStatus("not_invited");
    _saveStatusToStorage("not_invited");
    alert("Statut mis à jour : pas invitée");
  };

  return (

    <div className="min-h-screen bg-slate-100 p-8">

      <div className="max-w-5xl mx-auto">

        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-sm text-blue-600 hover:underline"
        >
          ← Retour
        </button>

        <div className="bg-white rounded-3xl shadow p-8">

          <h1 className="text-3xl font-bold mb-4">
            Générer un message LinkedIn
          </h1>

          {person.name && (
            <div className="mb-6 p-4 bg-slate-50 rounded-2xl">

              <h2 className="font-bold text-lg">
                {person.name}
              </h2>

              {person.headline && (
                <p className="text-gray-600">
                  {person.headline}
                </p>
              )}

              {person.profile_link && (
                <a
                  href={person.profile_link}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 text-sm hover:underline"
                >
                  Voir le profil LinkedIn
                </a>
              )}

              <div className="mt-3 flex items-center gap-3">
                <span className={`px-2 py-1 rounded-full text-sm ${inviteStatus === 'invited' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                  {inviteStatus === 'invited' ? 'Invitée' : 'Pas invitée'}
                </span>

                <button
                  onClick={markInvited}
                  className="bg-blue-600 text-white px-3 py-1 rounded-xl"
                >
                  Marquer invitée
                </button>

                <button
                  onClick={markNotInvited}
                  className="bg-gray-200 text-gray-800 px-3 py-1 rounded-xl"
                >
                  Marquer pas invitée
                </button>
              </div>

            </div>
          )}

          <div className="grid gap-6">

            <div>

              <label className="block font-semibold mb-2">
                Description de l'entreprise
              </label>

              <textarea
                value={companyDescription}
                onChange={(e) =>
                  setCompanyDescription(
                    e.target.value
                  )
                }
                rows={6}
                placeholder="Collez la présentation de l'entreprise..."
                className="w-full border rounded-2xl p-4 resize-none"
              />

            </div>

            <div>

              <label className="block font-semibold mb-2">
                Description du poste
              </label>

              <textarea
                value={jobDescription}
                onChange={(e) =>
                  setJobDescription(
                    e.target.value
                  )
                }
                rows={8}
                placeholder="Collez l'offre d'emploi..."
                className="w-full border rounded-2xl p-4 resize-none"
              />

            </div>

            <button
              onClick={handleCreateMessage}
              disabled={loading}
              className="
                bg-blue-600
                text-white
                px-6
                py-3
                rounded-2xl
                hover:bg-blue-700
                disabled:opacity-50
              "
            >
              {loading
                ? "Génération..."
                : "Créer le message"}
            </button>

          </div>

        </div>

        {generatedMessage && (

          <div className="mt-8 bg-white rounded-3xl shadow p-8">

            <div className="flex justify-between items-center mb-4">

              <h2 className="text-2xl font-bold">
                Message généré
              </h2>

              <button
                onClick={() =>
                  navigator.clipboard.writeText(
                    generatedMessage
                  )
                }
                className="
                  bg-green-600
                  text-white
                  px-4
                  py-2
                  rounded-xl
                "
              >
                Copier
              </button>

            </div>

            <pre
              className="
                whitespace-pre-wrap
                text-sm
                leading-7
                text-gray-800
              "
            >
              {generatedMessage}
            </pre>

          </div>

        )}

      </div>

    </div>

  );
}