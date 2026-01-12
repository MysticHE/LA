import { useState, useEffect, useCallback } from "react"

interface UseCountdownReturn {
  secondsLeft: number
  isActive: boolean
  start: (seconds: number) => void
  stop: () => void
  reset: () => void
}

/**
 * Hook for countdown timer, useful for rate limit countdowns
 * @returns Countdown state and controls
 */
export function useCountdown(): UseCountdownReturn {
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [isActive, setIsActive] = useState(false)

  useEffect(() => {
    if (!isActive || secondsLeft <= 0) {
      if (secondsLeft === 0 && isActive) {
        setIsActive(false)
      }
      return
    }

    const intervalId = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          setIsActive(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(intervalId)
  }, [isActive, secondsLeft])

  const start = useCallback((seconds: number) => {
    setSecondsLeft(seconds)
    setIsActive(true)
  }, [])

  const stop = useCallback(() => {
    setIsActive(false)
  }, [])

  const reset = useCallback(() => {
    setSecondsLeft(0)
    setIsActive(false)
  }, [])

  return {
    secondsLeft,
    isActive,
    start,
    stop,
    reset,
  }
}
