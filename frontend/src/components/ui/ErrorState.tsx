import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { theme } from '@/config/theme'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-12 px-4 rounded-lg"
      style={{
        backgroundColor: theme.colors.background.elevated,
        border: `1px solid ${theme.colors.border.subtle}`,
      }}
    >
      <AlertCircle size={48} style={{ color: theme.colors.error }} className="mb-4" />
      <h3
        className="text-lg font-semibold mb-2"
        style={{ color: theme.colors.text.primary }}
      >
        Something went wrong
      </h3>
      <p
        className="text-sm mb-6 text-center max-w-md"
        style={{ color: theme.colors.text.secondary }}
      >
        {message}
      </p>
      {onRetry && (
        <Button
          onClick={onRetry}
          className="flex items-center space-x-2"
          style={{
            backgroundColor: theme.colors.primary,
            color: '#FFFFFF',
          }}
        >
          <RefreshCw size={16} />
          <span>Try Again</span>
        </Button>
      )}
    </div>
  )
}
