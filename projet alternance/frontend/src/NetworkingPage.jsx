import React from "react";
import { useNavigate, useParams } from "react-router-dom";

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

function AddManualPersonModal({ company, onAdd, onClose }) {
  const [name,        setName]        = React.useState("");
  const [headline,    setHeadline]    = React.useState("");
  const [profileLink, setProfileLink] = React.useState("");
  const [location,    setLocation]    = React.useState("");
  const [error,       setError]       = React.useState("");

  const handleSubmit = () => {
    if (!name.trim()) { setError("Le nom est obligatoire."); return; }
    onAdd({
      name:            name.trim(),
      headline:        headline.trim(),
      profile_link:    profileLink.trim(),
      location:        location.trim(),
      current_company: company,
      status:          "not_invited",
      savedForCompany: company,
      manual:          true,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Ajouter un contact manuellement</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-semibold mb-1">Nom <span className="text-red-500">*</span></label>
            <input value={name} onChange={(e) => { setName(e.target.value); setError(""); }}
              placeholder="Jean Dupont" className="w-full border rounded-xl px-4 py-2.5 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Poste / Titre</label>
            <input value={headline} onChange={(e) => setHeadline(e.target.value)}
              placeholder="Responsable RH, Directeur technique…" className="w-full border rounded-xl px-4 py-2.5 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">URL LinkedIn (ou autre)</label>
            <input value={profileLink} onChange={(e) => setProfileLink(e.target.value)}
              placeholder="https://www.linkedin.com/in/..." className="w-full border rounded-xl px-4 py-2.5 text-sm" />
            <p className="text-xs text-slate-400 mt-1">Peut aussi être une URL d'un autre réseau.</p>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Ville</label>
            <input value={location} onChange={(e) => setLocation(e.target.value)}
              placeholder="Montpellier" className="w-full border rounded-xl px-4 py-2.5 text-sm" />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={handleSubmit}
            className="bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 font-semibold text-sm">
            Ajouter
          </button>
          <button onClick={onClose}
            className="bg-slate-200 text-slate-700 px-5 py-2.5 rounded-xl hover:bg-slate-300 text-sm">
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
}

function CompanyContactsCard({ contacts, onClose }) {
  const CONFIDENCE = {
    high:   { label: "Fiable",    cls: "bg-emerald-100 text-emerald-700" },
    medium: { label: "Partiel",   cls: "bg-amber-100 text-amber-700" },
    low:    { label: "Incertain", cls: "bg-red-100 text-red-700" },
  };
  const conf = CONFIDENCE[contacts.confidence] || CONFIDENCE.low;

  const copyToClipboard = (text) => {
    navigator.clipboard?.writeText(text).catch(() => {});
  };

  const fields = [
    { icon: "🌐", label: "Site web",           key: "website",          href: true },
    { icon: "💼", label: "Page carrières",     key: "careers_url",      href: true },
    { icon: "📝", label: "Formulaire contact", key: "contact_form_url", href: true },
    { icon: "📧", label: "Email RH",           key: "hr_email",         href: false },
    { icon: "📞", label: "Téléphone",          key: "hr_phone",         href: false },
    { icon: "🔗", label: "LinkedIn",           key: "linkedin_url",     href: true },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 mb-8 overflow-hidden">

      <div className="bg-gradient-to-r from-teal-700 to-teal-600 px-6 py-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-white font-bold text-lg">{contacts.company_name}</h2>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${conf.cls}`}>
              {conf.label}
            </span>
          </div>
          {contacts.sector && <p className="text-teal-200 text-sm">📌 {contacts.sector}</p>}
          {contacts.headquarters && <p className="text-teal-200 text-sm">📍 {contacts.headquarters}</p>}
          {contacts.description && <p className="text-teal-100 text-xs mt-2 leading-relaxed">{contacts.description}</p>}
        </div>
        <button onClick={onClose} className="text-teal-200 hover:text-white text-xl leading-none ml-4">✕</button>
      </div>

      <div className="p-5 space-y-5">

        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Informations de contact</h3>
          <div className="space-y-2">
            {fields.map(({ icon, label, key, href }) => {
              const value = contacts[key];
              if (!value) return null;
              return (
                <div key={key} className="flex items-center gap-3 py-1.5 border-b border-slate-100 last:border-0">
                  <span className="text-base shrink-0">{icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-400">{label}</p>
                    {href ? (
                      <a href={value} target="_blank" rel="noreferrer"
                        className="text-sm text-blue-600 hover:underline break-all font-medium">
                        {value}
                      </a>
                    ) : (
                      <p className="text-sm text-gray-800 font-medium break-all">{value}</p>
                    )}
                  </div>
                  <button onClick={() => copyToClipboard(value)}
                    title="Copier" className="text-slate-300 hover:text-slate-500 text-xs shrink-0">📋</button>
                </div>
              );
            })}
          </div>
          {!fields.some(f => contacts[f.key]) && (
            <p className="text-sm text-gray-400 italic">Aucun contact direct trouvé.</p>
          )}
        </div>

        {contacts.emails?.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              Emails trouvés ({contacts.emails.length})
            </h3>
            <div className="space-y-1">
              {contacts.emails.map((email, i) => (
                <div key={i} className="flex items-center gap-2">
                  <a href={`mailto:${email}`} className="text-sm text-blue-600 hover:underline">{email}</a>
                  <button onClick={() => copyToClipboard(email)}
                    className="text-slate-300 hover:text-slate-500 text-xs">📋</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {contacts.phones?.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              Téléphones trouvés ({contacts.phones.length})
            </h3>
            <div className="space-y-1">
              {contacts.phones.map((phone, i) => (
                <div key={i} className="flex items-center gap-2">
                  <a href={`tel:${phone}`} className="text-sm text-blue-600 hover:underline">{phone}</a>
                  <button onClick={() => copyToClipboard(phone)}
                    className="text-slate-300 hover:text-slate-500 text-xs">📋</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {contacts.contact_tips?.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Conseils de relance</h3>
            <ul className="space-y-1.5">
              {contacts.contact_tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-teal-500 font-bold shrink-0 mt-0.5">→</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function AddedPersonCard({ person, company, onRemove, onNavigate }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5">
      <div className="flex flex-col md:flex-row md:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-bold text-xl">{person.name || "Nom inconnu"}</h2>
            {person.manual && (
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">Manuel</span>
            )}
          </div>
          {person.headline && <p className="text-gray-700 mt-1">{person.headline}</p>}
          {person.current_company && <p className="text-sm text-gray-500 mt-1">🏢 {person.current_company}</p>}
          {person.location && <p className="text-sm text-gray-500">📍 {person.location}</p>}
          <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${
            person.status === "invited" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
          }`}>
            {person.status === "invited" ? "Invité(e)" : "Pas encore invité(e)"}
          </span>
        </div>
        <div className="flex flex-col gap-2 md:items-end shrink-0">
          {person.profile_link && (
            <a href={person.profile_link} target="_blank" rel="noreferrer"
              className="bg-blue-600 text-white px-4 py-2 rounded-xl text-center text-sm hover:bg-blue-700">
              Voir profil
            </a>
          )}
          <button onClick={() => onNavigate(person, company)}
            className="bg-green-600 text-white px-4 py-2 rounded-xl text-sm hover:bg-green-700">
            Message de relance
          </button>
          <button onClick={() => onRemove(person)}
            className="bg-red-600 text-white px-4 py-2 rounded-xl text-sm hover:bg-red-700">
            Retirer de la relance
          </button>
        </div>
      </div>
    </div>
  );
}

function SearchResultCard({ person, isAdded, onAdd }) {
  return (
    <div className="bg-white rounded-2xl shadow hover:shadow-lg transition p-5">
      <div className="flex flex-col md:flex-row md:justify-between gap-4">
        <div className="flex-1">
          <h2 className="font-bold text-xl">{person.name || "Nom inconnu"}</h2>
          {person.headline && <p className="text-gray-700 mt-1">{person.headline}</p>}
          {person.current_company && <p className="text-sm text-gray-500 mt-1">🏢 {person.current_company}</p>}
          {person.location && <p className="text-sm text-gray-500">📍 {person.location}</p>}
          {person.connections && <p className="text-sm text-gray-500">👥 {person.connections} connexions</p>}
        </div>
        <div className="flex flex-col gap-2 shrink-0">
          {person.profile_link && (
            <a href={person.profile_link} target="_blank" rel="noreferrer"
              className="bg-blue-600 text-white px-4 py-2 rounded-xl text-center text-sm hover:bg-blue-700">
              Voir LinkedIn
            </a>
          )}
          <button onClick={() => onAdd(person)} disabled={isAdded}
            className="bg-green-600 text-white px-4 py-2 rounded-xl text-sm hover:bg-green-700 disabled:opacity-50">
            {isAdded ? "✓ Ajouté" : "Ajouter à la relance"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function NetworkingPage({ applications }) {
  const { id }   = useParams();
  const navigate = useNavigate();

  const [company,       setCompany]       = React.useState("");
  const [location,      setLocation]      = React.useState("");
  const [maxResults,    setMaxResults]    = React.useState(100);
  const [people,        setPeople]        = React.useState([]);
  const [loading,       setLoading]       = React.useState(false);
  const [showModal,     setShowModal]     = React.useState(false);

  const [companyContacts,     setCompanyContacts]     = React.useState(null);
  const [loadingContacts,     setLoadingContacts]     = React.useState(false);
  const [contactsError,       setContactsError]       = React.useState(null);

  const [addedPeople, setAddedPeople] = React.useState(() => loadAddedPeople());

  React.useEffect(() => {
    if (!applications?.length || !id) return;
    const app = applications.find((a) => String(a.id) === String(id));
    if (app?.company) setCompany(app.company);
  }, [applications, id]);

  React.useEffect(() => { persistAddedPeople(addedPeople); }, [addedPeople]);


  const addToRelance = (person) => {
    setAddedPeople((prev) => {
      const already = prev.some(
        (item) => item.savedForCompany === company &&
          (item.profile_link === person.profile_link || item.id === person.id)
      );
      if (already) return prev;
      return [...prev, { ...person, status: "not_invited", savedForCompany: company }];
    });
  };

  const addManualPerson = (person) => {
    setAddedPeople((prev) => {
      const already = prev.some(
        (item) => item.savedForCompany === company &&
          item.name?.toLowerCase() === person.name?.toLowerCase()
      );
      if (already) { alert("Un contact avec ce nom existe déjà."); return prev; }
      return [...prev, person];
    });
  };

  const removeFromRelance = (person) => {
    setAddedPeople((prev) =>
      prev.filter((item) => !(
        item.savedForCompany === person.savedForCompany &&
        (item.profile_link === person.profile_link || item.id === person.id ||
         (person.manual && item.name === person.name))
      ))
    );
  };


  const searchPeople = async () => {
    if (!company.trim()) { alert("Entreprise manquante."); return; }
    setLoading(true);
    try {
      const res  = await fetch("http://localhost:8000/search-company-contacts", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          company, location, role: "",
          max_results: Math.min(100, Math.max(1, maxResults)),
        }),
      });
      const data = await res.json();
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


  const searchCompanyContacts = async () => {
    if (!company.trim()) { alert("Entreprise manquante."); return; }
    setLoadingContacts(true);
    setContactsError(null);
    setCompanyContacts(null);
    try {
      const res  = await fetch("http://localhost:8000/company-contacts", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ company }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setCompanyContacts(data);
    } catch (err) {
      setContactsError(err.message);
    } finally {
      setLoadingContacts(false);
    }
  };


  const companyAddedPeople = addedPeople.filter((p) => p.savedForCompany === company);
  const isAdded = (person) =>
    addedPeople.some((item) => item.profile_link === person.profile_link || item.id === person.id);


  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <div className="max-w-4xl mx-auto">

        <div className="relative mb-6">
          <button onClick={() => navigate(-1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:underline">
            ← Retour
          </button>
          <h1 className="text-4xl font-bold text-center">Gestion / Relance #{id}</h1>
        </div>
        <p className="text-gray-600 mb-8 text-center">
          Trouvez les recruteurs, RH et contacts de l'entreprise ciblée.
        </p>

        <div className="bg-white rounded-2xl shadow p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
            <div className="border rounded-xl p-3 bg-slate-50">
              <p className="text-xs text-gray-500 mb-1">Entreprise sélectionnée</p>
              <p className="font-medium">{company || "Chargement…"}</p>
            </div>
            <input value={location} onChange={(e) => setLocation(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchPeople()}
              placeholder="Ville (Montpellier)" className="border rounded-xl p-3 text-sm" />
            <input type="number" value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              min={1} max={100} placeholder="Nombre max de résultats"
              className="border rounded-xl p-3 text-sm" />
          </div>

          <div className="flex gap-3 flex-wrap">
            <button onClick={searchPeople} disabled={loading}
              className="bg-blue-600 text-white px-5 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 font-semibold text-sm">
              {loading ? "Recherche…" : "🔍 Rechercher sur LinkedIn"}
            </button>

            <button onClick={searchCompanyContacts} disabled={loadingContacts || !company.trim()}
              className="bg-teal-600 text-white px-5 py-3 rounded-xl hover:bg-teal-700 disabled:opacity-50 font-semibold text-sm">
              {loadingContacts ? "⏳ Recherche IA…" : "🤖 Contacts via IA"}
            </button>

            <button onClick={() => setShowModal(true)}
              className="bg-indigo-600 text-white px-5 py-3 rounded-xl hover:bg-indigo-700 font-semibold text-sm">
              + Ajouter manuellement
            </button>
          </div>

          <p className="text-xs text-gray-400 mt-3">
            <strong>LinkedIn</strong> : contacts de l'équipe RH/management. &nbsp;|&nbsp;
            <strong>IA</strong> : site, carrières, emails et téléphones de l'entreprise (nécessite GEMINI_API_KEY côté serveur).
          </p>
        </div>

        {loadingContacts && (
          <div className="bg-white rounded-2xl shadow p-8 text-center mb-8">
            <div className="text-3xl mb-2 animate-pulse">🤖</div>
            <p className="text-gray-600 font-medium">Recherche IA en cours pour <strong>{company}</strong>…</p>
            <p className="text-gray-400 text-sm mt-1">Gemini cherche le site, les emails, téléphones et formulaires de contact.</p>
          </div>
        )}

        {contactsError && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-8 text-sm text-red-700">
            <p className="font-semibold mb-1">❌ Erreur de recherche IA</p>
            <p>{contactsError}</p>
            <p className="mt-2 text-xs text-red-500">
              Vérifiez que GEMINI_API_KEY est défini dans l'environnement du serveur.
            </p>
          </div>
        )}

        {companyContacts && !loadingContacts && (
          <CompanyContactsCard
            contacts={companyContacts}
            onClose={() => setCompanyContacts(null)}
          />
        )}

        {companyAddedPeople.length > 0 && (
          <div className="mb-8">
            <p className="text-xl font-bold mb-1">
              Contacts à relancer
              <span className="ml-2 text-sm font-normal text-gray-500">({companyAddedPeople.length})</span>
            </p>
            <p className="text-sm text-gray-500 mb-3">Contacts que vous souhaitez relancer pour cette candidature.</p>
            <div className="space-y-4">
              {companyAddedPeople.map((person, i) => (
                <AddedPersonCard
                  key={person.profile_link || person.name || i}
                  person={person}
                  company={company}
                  onRemove={removeFromRelance}
                  onNavigate={(p, c) =>
                    navigate("/candidature", { state: { person: p, status: p.status || "not_invited", company: c } })
                  }
                />
              ))}
            </div>
          </div>
        )}

        {people.length > 0 && (
          <>
            <p className="font-semibold text-gray-700 mb-3">{people.length} contact(s) trouvé(s) sur LinkedIn</p>
            <div className="space-y-4">
              {people.map((person, i) => (
                <SearchResultCard
                  key={person.id || i}
                  person={person}
                  isAdded={isAdded(person)}
                  onAdd={addToRelance}
                />
              ))}
            </div>
          </>
        )}

        {loading && (
          <div className="text-center py-12 text-gray-500">Recherche des contacts LinkedIn…</div>
        )}

        {!loading && !loadingContacts && people.length === 0 && companyAddedPeople.length === 0 && !companyContacts && (
          <div className="text-center py-10 text-gray-400">
            Aucun contact. Lancez une recherche LinkedIn, utilisez la recherche IA, ou ajoutez un contact manuellement.
          </div>
        )}
      </div>

      {showModal && (
        <AddManualPersonModal
          company={company}
          onAdd={addManualPerson}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}