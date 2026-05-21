import React from "react";
import { useParams } from "react-router-dom";

export default function NetworkingPage() {
  const { id } = useParams();

  const [link, setLink] = React.useState("");
  const [people, setPeople] = React.useState([]);
  const [loading, setLoading] = React.useState(false);

  const handleScrape = async () => {
    try {
      setLoading(true);

      const res = await fetch(
        "http://localhost:8000/scrape-linkedin",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            url: link
          })
        }
      );

      const data = await res.json();

      setPeople(data.people || []);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">

      <h1 className="text-4xl font-bold text-center mb-8">
        Gestion / Relance candidature #{id}
      </h1>

      <div className="bg-white rounded-2xl shadow p-6 mb-8">

        <input
          value={link}
          onChange={(e) =>
            setLink(e.target.value)
          }
          placeholder="Coller le lien à scraper"
          className="border rounded-xl p-3 w-full mb-4"
        />

        <button
          onClick={handleScrape}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700"
        >
          Scraper
        </button>

      </div>

      {loading && (
        <p className="text-center">
          Scraping...
        </p>
      )}

      <div className="grid gap-4">

        {people.map((person, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow p-4 flex justify-between"
          >
            <div>
              <h2 className="font-bold">
                {person.name}
              </h2>

              <p>{person.role}</p>
            </div>

            <a
              href={person.linkedin}
              target="_blank"
              rel="noreferrer"
              className="bg-green-600 text-white px-4 py-2 rounded-xl"
            >
              Connecter
            </a>
          </div>
        ))}

      </div>
    </div>
  );
}