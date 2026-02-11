import * as React from "react"
import { cn } from "@/lib/utils"

interface StatisticProps {
  title?: React.ReactNode
  value?: React.ReactNode
  suffix?: React.ReactNode
  prefix?: React.ReactNode
  className?: string
  valueStyle?: React.CSSProperties
  titleStyle?: React.CSSProperties
}

const Statistic = React.forwardRef<HTMLDivElement, StatisticProps>(
  ({ title, value, suffix, prefix, className, valueStyle, titleStyle }, ref) => (
    <div ref={ref} className={cn("flex flex-col", className)}>
      {title && (
        <div
          className="text-sm text-foreground-secondary mb-1"
          style={titleStyle}
        >
          {title}
        </div>
      )}
      <div className="flex items-baseline gap-1">
        {prefix && <span className="text-foreground-secondary mr-1">{prefix}</span>}
        <span className="text-2xl font-semibold text-foreground" style={valueStyle}>
          {value}
        </span>
        {suffix && <span className="text-sm text-foreground-secondary ml-1">{suffix}</span>}
      </div>
    </div>
  )
)
Statistic.displayName = "Statistic"

export { Statistic }
