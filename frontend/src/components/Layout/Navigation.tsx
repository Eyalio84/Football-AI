import { NavLink } from 'react-router-dom'
import { Home, Trophy, Users, MessageCircle, HelpCircle, Swords, Radio, TrendingUp, Target } from 'lucide-react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'

// Mobile bottom bar shows items with mobile: true (max 6), desktop shows all
const navItems = [
  { to: '/', label: 'GAMES', icon: Home, mobile: true },
  { to: '/standings', label: 'TABLE', icon: Trophy, mobile: true },
  { to: '/chat', label: 'CHAT', icon: MessageCircle, mobile: true },
  { to: '/predictions', label: 'PREDICT', icon: Target, mobile: true },
  { to: '/companion', label: 'LIVE', icon: Radio, mobile: true },
  { to: '/mood-timeline', label: 'MOOD', icon: TrendingUp, mobile: true },
  { to: '/trivia', label: 'TRIVIA', icon: HelpCircle, mobile: true },
  { to: '/debate', label: 'DEBATE', icon: Swords, mobile: false },
  { to: '/teams', label: 'CLUBS', icon: Users, mobile: false },
]

function NavItem({ to, label, icon: Icon, clubId, palette }: {
  to: string; label: string; icon: typeof Home;
  clubId: string | null; palette: { primary: string }
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-col sm:flex-row items-center sm:space-x-2 px-2 sm:px-3 py-1 sm:py-2 rounded-lg transition-all duration-200 font-display tracking-wide ${
          isActive ? 'font-bold' : 'font-medium'
        }`
      }
      style={({ isActive }) => ({
        backgroundColor: isActive
          ? (clubId ? palette.primary + '20' : theme.colors.primary + '20')
          : 'transparent',
        color: isActive
          ? (clubId ? palette.primary : theme.colors.primary)
          : theme.colors.text.secondary,
      })}
    >
      <Icon size={18} />
      {/* Mobile: tiny label below icon. Desktop: inline label */}
      <span className="text-[10px] sm:text-sm leading-tight">{label}</span>
    </NavLink>
  )
}

export function Navigation() {
  const { clubId, palette } = useClubTheme()

  return (
    <>
      {/* ─── Desktop Top Nav (hidden on mobile) ─── */}
      <nav
        className="hidden sm:block sticky top-0 z-50 border-b backdrop-blur-md"
        style={{
          backgroundColor: theme.colors.background.elevated + 'E6',
          borderColor: clubId ? palette.primary + '30' : theme.colors.border.subtle,
        }}
      >
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="flex items-center justify-between h-14">
            {/* Wordmark */}
            <NavLink to="/" className="flex items-center gap-2">
              <span
                className="font-display text-xl font-extrabold tracking-wide uppercase"
                style={{ color: clubId ? palette.primary : theme.colors.text.primary }}
              >
                FOOTBALL
              </span>
              <span
                className="font-display text-xl font-extrabold tracking-wide uppercase"
                style={{ color: theme.colors.text.secondary }}
              >
                AI
              </span>
              {clubId && (
                <div
                  className="h-0.5 w-4 rounded-full ml-1 self-end mb-1"
                  style={{ backgroundColor: palette.primary }}
                />
              )}
            </NavLink>

            {/* Desktop nav links */}
            <div className="flex items-center space-x-1">
              {navItems.map((item) => (
                <NavItem key={item.to} {...item} clubId={clubId} palette={palette} />
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* ─── Mobile Bottom Tab Bar (hidden on desktop) ─── */}
      <nav
        className="sm:hidden fixed bottom-0 left-0 right-0 z-50 border-t backdrop-blur-md"
        style={{
          backgroundColor: theme.colors.background.elevated + 'F0',
          borderColor: clubId ? palette.primary + '25' : theme.colors.border.subtle,
          paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        }}
      >
        <div className="flex items-center justify-around px-1 py-1.5">
          {navItems.filter(item => item.mobile).map((item) => (
            <NavItem key={item.to} {...item} clubId={clubId} palette={palette} />
          ))}
        </div>
      </nav>
    </>
  )
}
