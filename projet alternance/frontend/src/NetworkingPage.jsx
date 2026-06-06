import React from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function NetworkingPage({ applications }) {
  const { id } = useParams();
  const navigate = useNavigate();

  const [company, setCompany] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [maxResults, setMaxResults] = React.useState(100);

  React.useEffect(() => {
    if (!applications || applications.length === 0 || !id) {
      return;
    }

    const application = applications.find((app) => String(app.id) === String(id));
    if (application && application.company) {
      setCompany(application.company);
    }
  }, [applications, id]);

  const [people, setPeople] = React.useState([]);
  const STORAGE_KEY = "addedPeople";

  const loadAddedPeople = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  };

  const persistAddedPeople = (arr) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
    } catch (e) {}
  };

  const [addedPeople, setAddedPeople] = React.useState(() => loadAddedPeople());
  const [loading, setLoading] = React.useState(false);

  const addToRelance = (person) => {
    setAddedPeople((prev) => {
      if (
        prev.some(
          (item) =>
            (item.profile_link === person.profile_link || item.id === person.id) && item.savedForCompany === company
        )
      ) {
        return prev;
      }
      const newPerson = { ...person, status: "not_invited", savedForCompany: company };
      const next = [...prev, newPerson];
      persistAddedPeople(next);
      return next;
    });
  };

  const removeFromRelance = (person) => {
    setAddedPeople((prev) => {
      const next = prev.filter(
        (item) => !(item.savedForCompany === person.savedForCompany && (item.profile_link === person.profile_link || item.id === person.id))
      );
      persistAddedPeople(next);
      return next;
    });
  };

  // keep localStorage in sync if state changes externally
  React.useEffect(() => {
    try {
      localStorage.setItem("addedPeople", JSON.stringify(addedPeople));
    } catch (e) {}
  }, [addedPeople]);

  const sendRelanceMessage = async (person) => {
    const message = `Bonjour ${person.name || ""},\n\nJe reviens vers vous concernant ma candidature pour une alternance. Je suis très intéressé par ce poste et disponible pour en discuter à votre convenance.\n\nBien cordialement.`;

    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(message);
      }
    } catch (err) {
      console.error("Impossible de copier le message de relance", err);
    }

    if (person.profile_link) {
      window.open(person.profile_link, "_blank");
    }

    alert(
      "Modèle de relance copié dans le presse-papier et profil LinkedIn ouvert."
    );
  };

  const searchPeople = async () => {
    if (!company.trim()) {
      alert("Impossible de trouver l'entreprise associée à cette candidature.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(
        "http://localhost:8000/search-company-contacts",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            company,
            location,
            role: "",
            max_results: Math.min(100, Math.max(1, maxResults)),
          }),
        }
      );

      const data = await res.json();

      console.log(data);

      // ensure addedPeople is current from storage
      const stored = loadAddedPeople();
      setAddedPeople(stored);

      const merged = (data.people || []).map((p) => {
        const found = stored.find(
          (s) => (s.profile_link === p.profile_link || s.id === p.id) && s.savedForCompany === company
        );
        return found ? { ...p, status: found.status } : p;
      });

      setPeople(merged);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="relative mb-6">
          <button
            onClick={() => navigate(-1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline"
          >
            ← Retour
          </button>
          <h1 className="text-4xl font-bold text-center">
            Gestion / Relance #{id}
          </h1>
        </div>

        <p className="text-gray-600 mb-8 text-center">
          Trouvez les recruteurs, RH et managers de
          l'entreprise ciblée.
        </p>

        <div className="bg-white rounded-2xl shadow p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border rounded-xl p-3 bg-slate-50">
              <p className="text-sm text-gray-500 mb-2">
                Entreprise sélectionnée
              </p>
              <p className="font-medium">
                {company || "Chargement..."}
              </p>
            </div>

            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && searchPeople()
              }
              placeholder="Ville (Montpellier)"
              className="border rounded-xl p-3"
            />

            <input
              type="number"
              value={maxResults}
              onChange={(e) =>
                setMaxResults(Number(e.target.value))
              }
              min={1}
              max={100}
              className="border rounded-xl p-3"
              placeholder="Nombre max de résultats"
            />
          </div>

          <button
            onClick={searchPeople}
            disabled={loading}
            className="mt-5 bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50"
          >
            {loading
              ? "Recherche en cours..."
              : "Rechercher"}
          </button>
          <p className="text-sm text-gray-500 mt-3">
            Le type de contact n'est pas limité pour cette recherche.
          </p>
        </div>

        {!loading && addedPeople.filter(p => p.savedForCompany === company).length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xl font-bold">Personnes ajoutées à la relance</p>
                <p className="text-sm text-gray-500">
                  Gérez les contacts que vous souhaitez relancer.
                </p>
              </div>
            </div>

            <div className="grid gap-4">
              {addedPeople.filter(p => p.savedForCompany === company).map((person, index) => (
                <div
                  key={person.profile_link || person.id || index}
                  className="bg-white rounded-2xl shadow p-5"
                >
                  <div className="flex flex-col md:flex-row md:justify-between gap-4">
                    <div className="flex-1">
                      <h2 className="font-bold text-xl">
                        {person.name || "Nom inconnu"}
                      </h2>

                      <p className="text-gray-700 mt-2">
                        {person.headline ||
                          "Aucune description disponible"}
                      </p>

                      {person.current_company && (
                        <p className="text-sm text-gray-500 mt-2">
                          🏢 {person.current_company}
                        </p>
                      )}

                      {person.location && (
                        <p className="text-sm text-gray-500">
                          📍 {person.location}
                        </p>
                      )}
                      {person.status && (
                        <p className="text-sm mt-2">
                          <span className={`px-2 py-1 rounded-full text-sm ${person.status === 'invited' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {person.status === 'invited' ? 'Invitée' : 'Pas invitée'}
                          </span>
                        </p>
                      )}
                    </div>

                    <div className="flex flex-col gap-2 md:items-end">
                      <button
                        onClick={() => removeFromRelance(person)}
                        className="bg-red-600 text-white px-4 py-2 rounded-xl hover:bg-red-700"
                      >
                        Retirer de la relance
                      </button>

                      {person.profile_link && (
                        <a
                          href={person.profile_link}
                          target="_blank"
                          rel="noreferrer"
                          className="bg-blue-600 text-white px-4 py-2 rounded-xl text-center hover:bg-blue-700"
                        >
                          Voir LinkedIn
                        </a>
                      )}

                      <button
                                        onClick={() =>
                                          navigate("/candidature", {
                                            state: { person, status: person.status || "not_invited", company },
                                          })
                        }
                        className="bg-green-600 text-white px-4 py-2 rounded-xl hover:bg-green-700"
                      >
                        Message de relance candidature
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && people.length > 0 && (
          <div className="mb-4">
            <p className="font-semibold text-gray-700">
              {people.length} contact(s) trouvé(s)
            </p>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <p className="text-lg">
              Recherche des contacts LinkedIn...
            </p>
          </div>
        )}

        <div className="grid gap-4">
          {people.map((person, index) => (
            <div
              key={person.id || index}
              className="bg-white rounded-2xl shadow hover:shadow-lg transition p-5"
            >
              <div className="flex flex-col md:flex-row md:justify-between gap-4">
                <div className="flex-1">
                  <h2 className="font-bold text-xl">
                    {person.name || "Nom inconnu"}
                  </h2>

                  <p className="text-gray-700 mt-2">
                    {person.headline ||
                      "Aucune description disponible"}
                  </p>

                  {person.current_company && (
                    <p className="text-sm text-gray-500 mt-2">
                      🏢 {person.current_company}
                    </p>
                  )}

                  {person.location && (
                    <p className="text-sm text-gray-500">
                      📍 {person.location}
                    </p>
                  )}

                  {person.connections && (
                    <p className="text-sm text-gray-500">
                      👥 {person.connections} connexions
                    </p>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  {person.profile_link && (
                    <a
                      href={person.profile_link}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-blue-600 text-white px-4 py-2 rounded-xl text-center hover:bg-blue-700"
                    >
                      Voir LinkedIn
                    </a>
                  )}

                  <button
                    onClick={() => addToRelance(person)}
                    disabled={addedPeople.some(
                      (item) =>
                        item.profile_link === person.profile_link ||
                        item.id === person.id
                    )}
                    className="bg-green-600 text-white px-4 py-2 rounded-xl hover:bg-green-700 disabled:opacity-50"
                  >
                    {addedPeople.some(
                      (item) =>
                        item.profile_link === person.profile_link ||
                        item.id === person.id
                    )
                      ? "Ajouté"
                      : "Ajouter à la relance"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {!loading && people.length === 0 && (
          <div className="text-center py-10 text-gray-500">
            Aucun contact trouvé
          </div>
        )}
      </div>
    </div>
  );
}