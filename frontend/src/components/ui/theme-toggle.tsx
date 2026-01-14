import { Moon, Sun, Monitor } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'
import { Button } from './button'

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  const cycleTheme = () => {
    const themes = ['light', 'dark', 'system'] as const
    const currentIndex = themes.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }

  const icon = {
    light: <Sun className="h-4 w-4" />,
    dark: <Moon className="h-4 w-4" />,
    system: <Monitor className="h-4 w-4" />,
  }[theme]

  const label = {
    light: 'Light mode',
    dark: 'Dark mode',
    system: 'System theme',
  }[theme]

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      title={label}
      aria-label={label}
    >
      {icon}
    </Button>
  )
}
