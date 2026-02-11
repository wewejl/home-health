import * as React from "react"
import { Moon, Sun, Monitor } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const cycleTheme = () => {
    if (theme === "light") {
      setTheme("dark")
    } else if (theme === "dark") {
      setTheme("system")
    } else {
      setTheme("light")
    }
  }

  const getIcon = () => {
    if (theme === "light") {
      return <Sun className="h-[1.2rem] w-[1.2rem]" />
    }
    if (theme === "dark") {
      return <Moon className="h-[1.2rem] w-[1.2rem]" />
    }
    return <Monitor className="h-[1.2rem] w-[1.2rem]" />
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      title={`当前主题: ${theme === "system" ? "跟随系统" : theme === "light" ? "浅色" : "深色"}`}
    >
      {getIcon()}
      <span className="sr-only">切换主题</span>
    </Button>
  )
}
