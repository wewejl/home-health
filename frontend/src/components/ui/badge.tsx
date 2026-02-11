import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/10 text-primary border-primary/20 hover:bg-primary/15",
        secondary:
          "border-transparent bg-secondary text-foreground-secondary border-border",
        destructive:
          "border-transparent bg-danger-light/80 text-danger border-danger/20",
        outline: "text-foreground border-border",
        primary:
          "border-transparent bg-primary/10 text-primary border-primary/20 hover:bg-primary/15",
        // 医疗状态颜色 - 浅色背景，深色文字
        success:
          "border-transparent bg-success-light/80 text-success border-success/20",
        warning:
          "border-transparent bg-warning-light/80 text-warning border-warning/20",
        danger:
          "border-transparent bg-danger-light/80 text-danger border-danger/20",
        info:
          "border-transparent bg-info-light/80 text-info border-info/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
