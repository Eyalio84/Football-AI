import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ChatPage } from './components/chat/ChatPage';
import { StandingsPage } from './components/standings/StandingsPage';
import { FixturesPage } from './components/fixtures/FixturesPage';
import { PredictionsPage } from './components/predictions/PredictionsPage';
import { ClubProvider } from './hooks/useClub';

const App: React.FC = () => {
  return (
    <ClubProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/chat" element={<Navigate to="/" replace />} />
            <Route path="/standings" element={<StandingsPage />} />
            <Route path="/fixtures" element={<FixturesPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
          </Routes>
        </Layout>
      </Router>
    </ClubProvider>
  );
};

export default App;