/**
 * App Component
 *
 * Root component that sets up the multi-view application with routing.
 * Uses React Router for navigation between Dashboard, Standings, Teams, and Chat.
 */

import { AppRoutes } from './routes'

function App() {
  return <AppRoutes />
}

export default App
