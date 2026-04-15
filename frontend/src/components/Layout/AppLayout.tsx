import { Outlet } from 'react-router-dom'
import { Navigation } from './Navigation'
import { LiveMatchBanner } from './LiveMatchBanner'
import { ConfigDrawer } from '@/components/Config/ConfigDrawer'
import { theme } from '@/config/theme'

export function AppLayout() {
  return (
    <div
      className="min-h-screen flex flex-col relative"
      style={{ backgroundColor: theme.colors.background.main }}
    >
      {/* Stadium floodlight glow — shifts with club theme */}
      <div className="club-glow fixed inset-0 pointer-events-none z-0" />

      {/* Config drawer — page-agnostic, lives outside route outlet */}
      <ConfigDrawer />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Navigation />
        {/* Live match banner — appears when your club is playing */}
        <LiveMatchBanner />
        {/* pb-20 on mobile for bottom tab bar clearance */}
        <main className="flex-1 container mx-auto px-4 py-6 pb-20 sm:pb-6 max-w-7xl">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
