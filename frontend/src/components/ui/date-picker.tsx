"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface DatePickerProps {
  value?: Date | null
  onChange?: (date: Date | null) => void
  disabled?: boolean
  className?: string
}

const DatePicker = React.forwardRef<HTMLDivElement, DatePickerProps>(
  ({ value, onChange, disabled = false, className }, ref) => {
    const [inputValue, setInputValue] = React.useState("")

    React.useEffect(() => {
      if (value) {
        setInputValue(formatDate(value))
      }
    }, [value])

    const formatDate = (date: Date): string => {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }

    const parseDate = (str: string): Date | null => {
      const match = str.match(/^(\d{4})-(\d{2})-(\d{2})$/)
      if (match) {
        return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]))
      }
      return null
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value
      setInputValue(val)

      if (val.length === 10) { // YYYY-MM-DD format
        const date = parseDate(val)
        if (date) {
          onChange?.(date)
        }
      }
    }

    const handleBlur = () => {
      const date = parseDate(inputValue)
      if (date) {
        onChange?.(date)
        setInputValue(formatDate(date))
      } else {
        if (value) {
          setInputValue(formatDate(value))
        }
      }
    }

    return (
      <div ref={ref} className={cn("relative", className)}>
        <div className="relative">
          <input
            type="date"
            value={inputValue}
            onChange={handleInputChange}
            onBlur={handleBlur}
            disabled={disabled}
            className={cn(
              "flex h-9 w-full rounded-sm border border-input bg-transparent px-3 py-1 text-sm shadow-sm",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "[&::-webkit-calendar-picker-indicator]:cursor-pointer"
            )}
          />
        </div>
      </div>
    )
  }
)
DatePicker.displayName = "DatePicker"

export { DatePicker }
