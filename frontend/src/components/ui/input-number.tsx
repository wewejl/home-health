import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

export interface InputNumberProps {
  id?: string
  value?: number
  onChange?: (value: number | null) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
  className?: string
}

const InputNumber = React.forwardRef<HTMLDivElement, InputNumberProps>(
  ({ value = 0, onChange, min, max, step = 1, disabled, className }, ref) => {
    const handleIncrement = () => {
      const newValue = value + step
      if (max === undefined || newValue <= max) {
        onChange?.(newValue)
      }
    }

    const handleDecrement = () => {
      const newValue = value - step
      if (min === undefined || newValue >= min) {
        onChange?.(newValue)
      }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseFloat(e.target.value)
      if (!isNaN(newValue)) {
        onChange?.(newValue)
      } else {
        onChange?.(null)
      }
    }

    return (
      <div ref={ref} className={cn("flex items-center border border-input rounded-md", className)}>
        <button
          type="button"
          onClick={handleDecrement}
          disabled={disabled || (min !== undefined && value <= min)}
          className={cn(
            "px-2 py-1 hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed",
            "border-r border-input"
          )}
        >
          <ChevronDown className="h-4 w-4" />
        </button>
        <input
          type="number"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          min={min}
          max={max}
          step={step}
          className={cn(
            "flex-1 w-full px-2 py-1 text-sm text-center",
            "focus:outline-none disabled:opacity-50",
            "[&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
          )}
        />
        <button
          type="button"
          onClick={handleIncrement}
          disabled={disabled || (max !== undefined && value >= max)}
          className={cn(
            "px-2 py-1 hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed",
            "border-l border-input"
          )}
        >
          <ChevronDown className="h-4 w-4 rotate-180" />
        </button>
      </div>
    )
  }
)
InputNumber.displayName = "InputNumber"

export { InputNumber }
