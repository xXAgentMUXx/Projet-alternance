import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import JobDashboard from "./JobDashboard";
import CoverLetterPage from "./CoverLetterPage";
import ApplicationsDashboard from "./ApplicationsDashboard";
import NetworkingPage from "./NetworkingPage";

export default function App() {
  const [applications, setApplications] = React.useState(() => {
    const saved = localStorage.getItem("applications");
    return saved ? JSON.parse(saved) : [];
  });

  React.useEffect(() => {
    localStorage.setItem(
      "applications",
      JSON.stringify(applications)
    );
  }, [applications]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <JobDashboard
              applications={applications}
              setApplications={setApplications}
            />
          }
        />

        <Route
          path="/cover-letter"
          element={<CoverLetterPage />}
        />
        <Route
          path="/networking/:id"
          element={<NetworkingPage />}
        />

        <Route
          path="/applications"
          element={
            <ApplicationsDashboard
              applications={applications}
              setApplications={setApplications}
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}