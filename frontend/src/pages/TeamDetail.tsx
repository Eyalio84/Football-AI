import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useTeam, useTeamFixtures, useTeamResults, useTeamPersonality } from '@/hooks/useTeams'
import { TeamDetail as TeamDetailComponent } from '@/components/Teams/TeamDetail'
import { Button } from '@/components/ui/button'
import { ErrorState } from '@/components/ui/ErrorState'
import { theme } from '@/config/theme'

export function TeamDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { team, loading: teamLoading, error: teamError, refetch: refetchTeam } = useTeam(id!)
  const { fixtures, loading: fixturesLoading } = useTeamFixtures(id!)
  const { results, loading: resultsLoading } = useTeamResults(id!)
  const { personality, loading: personalityLoading } = useTeamPersonality(id!)

  const handleBack = () => {
    navigate('/teams')
  }

  if (teamError) {
    return (
      <div>
        <Button
          onClick={handleBack}
          variant="ghost"
          className="mb-6"
        >
          <ArrowLeft size={16} className="mr-2" />
          Back to Teams
        </Button>
        <ErrorState message={teamError} onRetry={refetchTeam} />
      </div>
    )
  }

  if (teamLoading || !team) {
    return (
      <div>
        <Button
          onClick={handleBack}
          variant="ghost"
          className="mb-6"
        >
          <ArrowLeft size={16} className="mr-2" />
          Back to Teams
        </Button>
        <div
          className="text-center py-12"
          style={{ color: theme.colors.text.secondary }}
        >
          Loading team details...
        </div>
      </div>
    )
  }

  return (
    <div>
      <Button
        onClick={handleBack}
        variant="ghost"
        className="mb-6"
      >
        <ArrowLeft size={16} className="mr-2" />
        Back to Teams
      </Button>

      <TeamDetailComponent
        team={team}
        fixtures={fixtures}
        results={results}
        fixturesLoading={fixturesLoading}
        resultsLoading={resultsLoading}
        personality={personality}
        personalityLoading={personalityLoading}
      />
    </div>
  )
}
