import React from "react";
import { useNavigate } from "react-router-dom";

export default function BlockedCompaniesPage({ blockedCompanies, setBlockedCompanies }) {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = React.useState("");

  const addCompany = () => {
    const company = inputValue.trim();
    if (!company) return;

    const normalized = company.toLowerCase();
    if (blockedCompanies.some((item) => item.toLowerCase() === normalized)) {
      setInputValue("");
      return;
    }

    setBlockedCompanies((prev) => [...prev, company]);
    setInputValue("");
  };

  const removeCompany = (companyToRemove) => {
    setBlockedCompanies((prev) =>
      prev.filter((company) => company.toLowerCase() !== companyToRemove.toLowerCase())
    );
  };

  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-sm text-blue-600 hover:underline"
        >
          ← Retour
        </button>

        <div className="bg-white rounded-3xl shadow p-8">
          <h1 className="text-3xl font-bold mb-4">Bloquer des entreprises</h1>
          <p className="text-gray-600 mb-6">
            Ajoutez ici des noms d'entreprises ou de sites que vous ne voulez plus voir
            dans les prochains résultats de recherche.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 mb-6">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addCompany()}
              placeholder="mydigitalschool, Studi, Club Med..."
              className="flex-1 border rounded-2xl p-4"
            />
            <button
              onClick={addCompany}
              className="bg-red-600 text-white px-6 py-3 rounded-2xl hover:bg-red-700"
            >
              Ajouter
            </button>
          </div>

          {blockedCompanies.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-center text-gray-500">
              Aucune entreprise bloquée pour le moment.
            </div>
          ) : (
            <div className="grid gap-3">
              {blockedCompanies.map((company) => (
                <div
                  key={company}
                  className="flex items-center justify-between gap-3 rounded-2xl border p-4"
                >
                  <span className="text-sm font-medium">{company}</span>
                  <button
                    onClick={() => removeCompany(company)}
                    className="bg-slate-200 text-slate-800 px-4 py-2 rounded-xl hover:bg-slate-300"
                  >
                    Retirer
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
