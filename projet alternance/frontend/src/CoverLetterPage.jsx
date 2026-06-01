import React, { useState } from "react";
import { saveAs } from "file-saver";
import {
  Document,
  Packer,
  Paragraph,
  TextRun
} from "docx";
import jsPDF from "jspdf";

export default function CoverLetterPage() {
  const [companyDescription, setCompanyDescription] =
    useState("");

  const [jobDescription, setJobDescription] =
    useState("");

  const [templateFile, setTemplateFile] =
    useState(null);

  const [generatedLetter, setGeneratedLetter] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  async function generateLetter() {
    if (!templateFile) {
      alert("Ajoute un template PDF ou DOCX");
      return;
    }

    try {
      setLoading(true);

      const formData = new FormData();

      formData.append(
        "job_description",
        jobDescription
      );

      formData.append(
        "company_description",
        companyDescription
      );

      formData.append(
        "template_file",
        templateFile
      );

      const res = await fetch(
        "http://localhost:8000/generate-letter",
        {
          method: "POST",
          body: formData
        }
      );

      const data = await res.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      setGeneratedLetter(data.letter);

    } catch (err) {
      console.error(err);
      alert("Erreur backend");
    } finally {
      setLoading(false);
    }
  }

  async function exportDocx() {
    const doc = new Document({
      sections: [
        {
          children:
            generatedLetter
              .split("\n")
              .map(
                (line) =>
                  new Paragraph({
                    children: [
                      new TextRun({
                        text: line,
                        font: "Arial",
                        size: 20
                      })
                    ]
                  })
              )
        }
      ]
    });

    const blob =
      await Packer.toBlob(doc);

    saveAs(
      blob,
      "lettre_motivation.docx"
    );
  }

  function exportPdf() {
    const pdf = new jsPDF();

    pdf.setFont("helvetica");
    pdf.setFontSize(10);

    const lines =
      pdf.splitTextToSize(
        generatedLetter,
        180
      );

    pdf.text(
      lines,
      15,
      20
    );

    pdf.save(
      "lettre_motivation.pdf"
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow p-8">

        <h1 className="text-3xl font-bold text-center mb-8">
          Générateur de Lettre de Motivation
        </h1>

        <div className="space-y-6">

          <div>
            <label className="block mb-2 font-semibold">
              Description entreprise
            </label>

            <textarea
              value={companyDescription}
              onChange={(e) =>
                setCompanyDescription(
                  e.target.value
                )
              }
              placeholder="Colle la description entreprise..."
              className="w-full h-40 border rounded-xl p-3"
            />
          </div>

          <div>
            <label className="block mb-2 font-semibold">
              Description du poste
            </label>

            <textarea
              value={jobDescription}
              onChange={(e) =>
                setJobDescription(
                  e.target.value
                )
              }
              placeholder="Colle la description du poste..."
              className="w-full h-40 border rounded-xl p-3"
            />
          </div>

          <div>
            <label className="block mb-2 font-semibold">
              Template PDF ou DOCX
            </label>

            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) =>
                setTemplateFile(
                  e.target.files[0]
                )
              }
              className="w-full border rounded-xl p-3"
            />

            {templateFile && (
              <p className="text-green-600 mt-2">
                ✓ {templateFile.name}
              </p>
            )}
          </div>

          <button
            onClick={generateLetter}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading
              ? "Génération..."
              : "Générer"}
          </button>

          {generatedLetter && (
            <>
              <div>
                <h2 className="text-2xl font-bold mb-4">
                  Lettre générée
                </h2>

                <textarea
                  value={generatedLetter}
                  onChange={(e) =>
                    setGeneratedLetter(
                      e.target.value
                    )
                  }
                  className="w-full h-96 border rounded-xl p-4"
                />
              </div>

              <div className="flex gap-4">

                <button
                  onClick={exportDocx}
                  className="bg-green-600 text-white px-5 py-3 rounded-xl hover:bg-green-700"
                >
                  Export DOCX
                </button>

                <button
                  onClick={exportPdf}
                  className="bg-red-600 text-white px-5 py-3 rounded-xl hover:bg-red-700"
                >
                  Export PDF
                </button>

              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
}