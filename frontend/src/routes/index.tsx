import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { Standings } from '@/pages/Standings'
import { Teams } from '@/pages/Teams'
import { TeamDetail } from '@/pages/TeamDetail'
import { Chat } from '@/pages/Chat'
import { Trivia } from '@/pages/Trivia'
import { Debate } from '@/pages/Debate'
import { Companion } from '@/pages/Companion'
import { Predictions } from '@/pages/Predictions'
import { MoodTimeline } from '@/pages/MoodTimeline'
import { PredictionCard } from '@/pages/PredictionCard'
import { Demo } from '@/pages/Demo'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="standings" element={<Standings />} />
        <Route path="teams" element={<Teams />} />
        <Route path="teams/:id" element={<TeamDetail />} />
        <Route path="chat" element={<Chat />} />
        <Route path="trivia" element={<Trivia />} />
        <Route path="debate" element={<Debate />} />
        <Route path="companion" element={<Companion />} />
        <Route path="predictions" element={<Predictions />} />
        <Route path="mood-timeline" element={<MoodTimeline />} />
      </Route>
      {/* Standalone pages — no nav bar */}
      <Route path="demo" element={<Demo />} />
      <Route path="card/:home/:away" element={<PredictionCard />} />
    </Routes>
  )
}
