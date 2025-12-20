import { useState, useCallback } from 'react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { API_URL } from '@/config/api'

interface TriviaQuestion {
  id: number
  question: string
  correct_answer: string
  wrong_answers: string[]
  category: string
  difficulty: string
  explanation: string
  team_id: number | null
}

interface CheckResult {
  correct: boolean
  correct_answer: string
  explanation: string
}

const CATEGORY_LABELS: Record<string, string> = {
  records: 'RECORDS',
  head2head: 'HEAD TO HEAD',
  history: 'HISTORY',
  stats: 'STATS',
  rivalries: 'RIVALRIES',
  legends: 'LEGENDS',
}

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: '#22c55e',
  medium: '#eab308',
  hard: '#ef4444',
}

export function Trivia() {
  const { palette } = useClubTheme()
  const [question, setQuestion] = useState<TriviaQuestion | null>(null)
  const [options, setOptions] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<CheckResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [category, setCategory] = useState<string>('')

  const fetchQuestion = useCallback(async () => {
    setLoading(true)
    setSelected(null)
    setResult(null)

    try {
      const url = category
        ? `${API_URL}/api/v1/trivia?category=${category}`
        : `${API_URL}/api/v1/trivia`
      const resp = await fetch(url)
      const json = await resp.json()
      const q = json.data as TriviaQuestion

      // Shuffle options
      let wrongs: string[] = []
      try {
        wrongs = typeof q.wrong_answers === 'string'
          ? JSON.parse(q.wrong_answers)
          : q.wrong_answers
      } catch {
        wrongs = []
      }

      const allOptions = [...wrongs, q.correct_answer]
        .sort(() => Math.random() - 0.5)

      setQuestion(q)
      setOptions(allOptions)
    } catch (err) {
      console.error('Failed to fetch trivia:', err)
    } finally {
      setLoading(false)
    }
  }, [category])

  const handleAnswer = async (answer: string) => {
    if (selected || !question) return
    setSelected(answer)

    try {
      const resp = await fetch(
        `${API_URL}/api/v1/trivia/check?question_id=${question.id}&answer=${encodeURIComponent(answer)}`,
        { method: 'POST' }
      )
      const json = await resp.json()
      const data = json.data as CheckResult
      setResult(data)
      setScore(prev => ({
        correct: prev.correct + (data.correct ? 1 : 0),
        total: prev.total + 1,
      }))
    } catch (err) {
      console.error('Failed to check answer:', err)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1
          className="font-display text-3xl font-extrabold tracking-wide uppercase"
          style={{ color: theme.colors.text.primary }}
        >
          TRIVIA
        </h1>
        {score.total > 0 && (
          <div
            className="font-mono text-sm px-3 py-1 rounded-lg"
            style={{
              backgroundColor: theme.colors.background.elevated,
              color: theme.colors.text.primary,
            }}
          >
            {score.correct}/{score.total}
            <span style={{ color: theme.colors.text.muted }}> correct</span>
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategory('')}
          className="px-3 py-1 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
          style={{
            backgroundColor: !category ? palette.primary + '25' : theme.colors.background.elevated,
            color: !category ? palette.primary : theme.colors.text.secondary,
            border: `1px solid ${!category ? palette.primary + '50' : 'transparent'}`,
          }}
        >
          ALL
        </button>
        {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setCategory(key)}
            className="px-3 py-1 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
            style={{
              backgroundColor: category === key ? palette.primary + '25' : theme.colors.background.elevated,
              color: category === key ? palette.primary : theme.colors.text.secondary,
              border: `1px solid ${category === key ? palette.primary + '50' : 'transparent'}`,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Question Card or Start */}
      {!question ? (
        <div
          className="rounded-xl p-10 text-center border"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
          }}
        >
          <p
            className="text-lg italic mb-6"
            style={{ color: theme.colors.text.secondary }}
          >
            Test your football knowledge across 136 questions mined from 230,000 matches.
          </p>
          <button
            onClick={fetchQuestion}
            disabled={loading}
            className="px-8 py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105 active:scale-95"
            style={{
              backgroundColor: palette.primary,
              color: palette.textOnPrimary,
            }}
          >
            {loading ? 'LOADING...' : 'START'}
          </button>
        </div>
      ) : (
        <div
          className="rounded-xl overflow-hidden border"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
          }}
        >
          {/* Question header */}
          <div
            className="px-5 py-3 flex items-center justify-between"
            style={{ backgroundColor: theme.colors.background.elevated }}
          >
            <span
              className="font-display text-xs font-bold tracking-widest uppercase"
              style={{ color: theme.colors.text.secondary }}
            >
              {CATEGORY_LABELS[question.category] || question.category}
            </span>
            <span
              className="font-mono text-xs font-semibold uppercase px-2 py-0.5 rounded"
              style={{
                color: DIFFICULTY_COLORS[question.difficulty] || '#6b7280',
                backgroundColor: (DIFFICULTY_COLORS[question.difficulty] || '#6b7280') + '15',
              }}
            >
              {question.difficulty}
            </span>
          </div>

          {/* Question text */}
          <div className="px-5 py-6">
            <p
              className="text-lg leading-relaxed mb-6"
              style={{ color: theme.colors.text.primary }}
            >
              {question.question}
            </p>

            {/* Options */}
            <div className="space-y-2">
              {options.map((opt, idx) => {
                const isSelected = selected === opt
                const isCorrectAnswer = result && opt === result.correct_answer
                const isWrong = isSelected && result && !result.correct

                let bg = theme.colors.background.elevated
                let border = 'transparent'
                let textColor = theme.colors.text.primary

                if (result) {
                  if (isCorrectAnswer) {
                    bg = 'rgba(34, 197, 94, 0.15)'
                    border = '#22c55e'
                    textColor = '#22c55e'
                  } else if (isWrong) {
                    bg = 'rgba(239, 68, 68, 0.15)'
                    border = '#ef4444'
                    textColor = '#ef4444'
                  }
                } else if (isSelected) {
                  bg = palette.primary + '20'
                  border = palette.primary
                }

                return (
                  <button
                    key={idx}
                    onClick={() => handleAnswer(opt)}
                    disabled={!!selected}
                    className="w-full text-left px-4 py-3 rounded-lg transition-all duration-200 border disabled:cursor-default"
                    style={{
                      backgroundColor: bg,
                      borderColor: border,
                      color: textColor,
                    }}
                  >
                    <span className="font-mono text-xs mr-2" style={{ color: theme.colors.text.muted }}>
                      {String.fromCharCode(65 + idx)}.
                    </span>
                    {opt}
                  </button>
                )
              })}
            </div>

            {/* Result */}
            {result && (
              <div className="mt-5 animate-message-in">
                <div
                  className="flex items-center gap-2 mb-2 font-display text-sm font-bold tracking-wide uppercase"
                  style={{ color: result.correct ? '#22c55e' : '#ef4444' }}
                >
                  {result.correct ? 'CORRECT' : 'WRONG'}
                </div>
                <p
                  className="text-sm italic"
                  style={{ color: theme.colors.text.secondary }}
                >
                  {result.explanation}
                </p>

                <button
                  onClick={fetchQuestion}
                  disabled={loading}
                  className="mt-4 px-6 py-2 rounded-lg font-display font-bold tracking-wide uppercase text-xs transition-all hover:scale-105"
                  style={{
                    backgroundColor: palette.primary,
                    color: palette.textOnPrimary,
                  }}
                >
                  {loading ? 'LOADING...' : 'NEXT QUESTION'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
