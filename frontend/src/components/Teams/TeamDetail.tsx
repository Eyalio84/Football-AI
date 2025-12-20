/**
 * TeamDetail Component
 *
 * Comprehensive team view with personality data.
 * Tabs: Overview, Legends, Rivalries, Moments, Graph
 */

import { useState } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { GameCard } from '@/components/Games/GameCard'
import { LegendsGrid } from './LegendsGrid'
import { RivalryDisplay } from './RivalryDisplay'
import { MomentsTimeline } from './MomentsTimeline'
import { MoodIndicator } from './MoodIndicator'
import { MapPin, User, Star, Swords, Trophy, Network, Calendar } from 'lucide-react'
import { theme } from '@/config/theme'
import { getKGViewerUrl } from '@/services/api'
import type { Team, Game, TeamPersonality } from '@/types'

interface TeamDetailProps {
  team: Team
  fixtures: Game[]
  results: Game[]
  fixturesLoading?: boolean
  resultsLoading?: boolean
  personality?: TeamPersonality | null
  personalityLoading?: boolean
}

// Get team initials for avatar
const getTeamInitials = (name: string) => {
  const words = name.split(' ').filter(w => w.length > 0)
  return words.map(w => w[0]).join('').slice(0, 3).toUpperCase()
}

export function TeamDetail({
  team,
  fixtures,
  results,
  fixturesLoading,
  resultsLoading,
  personality,
  personalityLoading,
}: TeamDetailProps) {
  const [activeTab, setActiveTab] = useState('overview')

  const handleOpenKGViewer = () => {
    const url = `${getKGViewerUrl()}?team=${team.id}`
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-6">
      {/* Team Header */}
      <div
        className="rounded-lg p-8"
        style={{
          backgroundColor: theme.colors.background.elevated,
          borderColor: theme.colors.border.subtle,
        }}
      >
        <div className="flex flex-col md:flex-row items-center md:items-start space-y-4 md:space-y-0 md:space-x-6">
          {/* Team Logo */}
          <Avatar className="h-24 w-24">
            <AvatarFallback
              className="text-2xl font-bold"
              style={{ backgroundColor: theme.colors.primary + '20' }}
            >
              {getTeamInitials(team.name)}
            </AvatarFallback>
          </Avatar>

          {/* Team Info */}
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-4 mb-2">
              <h1
                className="text-3xl font-bold"
                style={{ color: theme.colors.text.primary }}
              >
                {team.name}
              </h1>
              {/* Mood indicator in header */}
              {personality?.mood && (
                <MoodIndicator mood={personality.mood} size="sm" />
              )}
            </div>

            {/* Identity nickname if available */}
            {personality?.identity?.nickname && (
              <p
                className="text-lg italic mb-2"
                style={{ color: theme.colors.text.secondary }}
              >
                "{personality.identity.nickname}"
              </p>
            )}

            <div className="space-y-2">
              {team.stadium && (
                <div className="flex items-center justify-center md:justify-start space-x-2">
                  <MapPin size={16} style={{ color: theme.colors.text.secondary }} />
                  <span style={{ color: theme.colors.text.secondary }}>
                    {team.stadium}
                  </span>
                </div>
              )}

              {team.manager && (
                <div className="flex items-center justify-center md:justify-start space-x-2">
                  <User size={16} style={{ color: theme.colors.text.secondary }} />
                  <span style={{ color: theme.colors.text.secondary }}>
                    Manager: {team.manager}
                  </span>
                </div>
              )}

              {team.league && (
                <div className="flex items-center justify-center md:justify-start space-x-2">
                  <span
                    className="font-medium"
                    style={{ color: theme.colors.text.secondary }}
                  >
                    {team.league}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs: Overview, Legends, Rivalries, Moments, Graph */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full flex-wrap h-auto gap-1 p-1">
          <TabsTrigger value="overview" className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="legends" className="flex items-center gap-1">
            <Star className="h-4 w-4" />
            <span className="hidden sm:inline">Legends</span>
          </TabsTrigger>
          <TabsTrigger value="rivalries" className="flex items-center gap-1">
            <Swords className="h-4 w-4" />
            <span className="hidden sm:inline">Rivalries</span>
          </TabsTrigger>
          <TabsTrigger value="moments" className="flex items-center gap-1">
            <Trophy className="h-4 w-4" />
            <span className="hidden sm:inline">Moments</span>
          </TabsTrigger>
          <TabsTrigger value="graph" className="flex items-center gap-1">
            <Network className="h-4 w-4" />
            <span className="hidden sm:inline">Graph</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab - Fixtures & Results */}
        <TabsContent value="overview" className="mt-6 space-y-6">
          {/* Fixtures */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Upcoming Fixtures
            </h3>
            {fixturesLoading ? (
              <div
                className="text-center py-8"
                style={{ color: theme.colors.text.secondary }}
              >
                Loading fixtures...
              </div>
            ) : fixtures.length === 0 ? (
              <div
                className="text-center py-8 rounded-lg"
                style={{
                  backgroundColor: theme.colors.background.elevated,
                  border: `1px solid ${theme.colors.border.subtle}`,
                }}
              >
                <p style={{ color: theme.colors.text.secondary }}>
                  No upcoming fixtures
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {fixtures.slice(0, 4).map((game, index) => (
                  <GameCard key={game.id || index} game={game} />
                ))}
              </div>
            )}
          </div>

          {/* Results */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Recent Results
            </h3>
            {resultsLoading ? (
              <div
                className="text-center py-8"
                style={{ color: theme.colors.text.secondary }}
              >
                Loading results...
              </div>
            ) : results.length === 0 ? (
              <div
                className="text-center py-8 rounded-lg"
                style={{
                  backgroundColor: theme.colors.background.elevated,
                  border: `1px solid ${theme.colors.border.subtle}`,
                }}
              >
                <p style={{ color: theme.colors.text.secondary }}>
                  No recent results
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.slice(0, 4).map((game, index) => (
                  <GameCard key={game.id || index} game={game} />
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Legends Tab */}
        <TabsContent value="legends" className="mt-6">
          {personalityLoading ? (
            <div
              className="text-center py-8"
              style={{ color: theme.colors.text.secondary }}
            >
              Loading legends...
            </div>
          ) : (
            <LegendsGrid
              legends={personality?.legends || []}
              teamName={team.name}
            />
          )}
        </TabsContent>

        {/* Rivalries Tab */}
        <TabsContent value="rivalries" className="mt-6">
          {personalityLoading ? (
            <div
              className="text-center py-8"
              style={{ color: theme.colors.text.secondary }}
            >
              Loading rivalries...
            </div>
          ) : (
            <RivalryDisplay
              rivalries={personality?.rivalries || []}
              teamName={team.name}
            />
          )}
        </TabsContent>

        {/* Moments Tab */}
        <TabsContent value="moments" className="mt-6">
          {personalityLoading ? (
            <div
              className="text-center py-8"
              style={{ color: theme.colors.text.secondary }}
            >
              Loading moments...
            </div>
          ) : (
            <MomentsTimeline
              moments={personality?.moments || []}
              teamName={team.name}
            />
          )}
        </TabsContent>

        {/* Graph Tab */}
        <TabsContent value="graph" className="mt-6">
          <div
            className="text-center py-12 rounded-lg"
            style={{
              backgroundColor: theme.colors.background.elevated,
              border: `1px solid ${theme.colors.border.subtle}`,
            }}
          >
            <Network
              className="h-16 w-16 mx-auto mb-4"
              style={{ color: theme.colors.text.secondary }}
            />
            <h3
              className="text-lg font-semibold mb-2"
              style={{ color: theme.colors.text.primary }}
            >
              Knowledge Graph
            </h3>
            <p
              className="mb-4"
              style={{ color: theme.colors.text.secondary }}
            >
              Explore {team.name}'s connections to legends, rivalries, and moments.
            </p>
            <button
              onClick={handleOpenKGViewer}
              className="px-4 py-2 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: theme.colors.primary,
                color: '#fff',
              }}
            >
              Open Interactive Graph
            </button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
