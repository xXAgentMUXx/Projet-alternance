import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import JobDashboard from "./JobDashboard";
import CoverLetterPage from "./CoverLetterPage";
import ApplicationsDashboard from "./ApplicationsDashboard";
import NetworkingPage from "./NetworkingPage";
import CandidaturePage from "./CandidaturePage";
import BlockedCompaniesPage from "./BlockedCompaniesPage";
import NotificationSettings from "./NotificationSettings";
import SettingsPage from "./SettingsPage";

export default function App() {
  const [applications, setApplications] = React.useState(() => {
    const saved = localStorage.getItem("applications");
    return saved ? JSON.parse(saved) : [];
  });
  const [blockedCompanies, setBlockedCompanies] = React.useState(() => {
    const saved = localStorage.getItem("blockedCompanies");
    return saved ? JSON.parse(saved) : [];
  });

  React.useEffect(() => {
    localStorage.setItem(
      "applications",
      JSON.stringify(applications)
    );
  }, [applications]);

  React.useEffect(() => {
    localStorage.setItem(
      "blockedCompanies",
      JSON.stringify(blockedCompanies)
    );
  }, [blockedCompanies]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <JobDashboard
              applications={applications}
              setApplications={setApplications}
              blockedCompanies={blockedCompanies}
              setBlockedCompanies={setBlockedCompanies}
            />
          }
        />

        <Route
          path="/blocked-companies"
          element={
            <BlockedCompaniesPage
              blockedCompanies={blockedCompanies}
              setBlockedCompanies={setBlockedCompanies}
            />
          }
        />

        <Route
          path="/cover-letter"
          element={<CoverLetterPage />}
        />
        <Route
          path="/networking/:id"
          element={<NetworkingPage applications={applications} />}
        />

        <Route
          path="/candidature"
          element={<CandidaturePage />}
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
        <Route path="/notifications" element={<NotificationSettings applications={applications} />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  );
}