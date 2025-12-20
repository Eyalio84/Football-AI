import { Skeleton } from '@/components/ui/skeleton'
import { Card } from '@/components/ui/card'

export function GamesLoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Group 1 */}
      <div>
        <Skeleton className="h-8 w-32 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <GameCardSkeleton key={i} />
          ))}
        </div>
      </div>

      {/* Group 2 */}
      <div>
        <Skeleton className="h-8 w-40 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2].map((i) => (
            <GameCardSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  )
}

function GameCardSkeleton() {
  return (
    <Card className="p-4">
      {/* Status Badge */}
      <Skeleton className="h-6 w-20 mb-4" />

      {/* Teams */}
      <div className="space-y-3">
        {/* Home Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <Skeleton className="h-10 w-10 rounded-full" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-8 w-8" />
        </div>

        {/* Away Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <Skeleton className="h-10 w-10 rounded-full" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-8 w-8" />
        </div>
      </div>

      {/* Details */}
      <div className="mt-4 pt-4 border-t flex items-center justify-between">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-24" />
      </div>
    </Card>
  )
}

export function StandingsLoadingSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-3">
          <Skeleton className="h-4 w-6" />
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  )
}

export function TeamsLoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(8)].map((_, i) => (
        <Card key={i} className="p-6">
          <div className="flex flex-col items-center space-y-4">
            <Skeleton className="h-20 w-20 rounded-full" />
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-28" />
          </div>
        </Card>
      ))}
    </div>
  )
}
