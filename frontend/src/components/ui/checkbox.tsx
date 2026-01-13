import * as React from "react"
import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

export interface CheckboxProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, id, ...props }, ref) => {
    const inputId = id || React.useId()

    return (
      <div className="flex items-start gap-2">
        <div className="relative flex items-center justify-center">
          <input
            type="checkbox"
            id={inputId}
            ref={ref}
            className={cn(
              "peer h-4 w-4 shrink-0 appearance-none rounded-sm border border-primary",
              "ring-offset-background focus-visible:outline-none focus-visible:ring-2",
              "focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "checked:bg-primary checked:border-primary",
              className
            )}
            {...props}
          />
          <Check
            className={cn(
              "absolute h-3 w-3 text-primary-foreground pointer-events-none",
              "opacity-0 peer-checked:opacity-100"
            )}
          />
        </div>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm leading-tight cursor-pointer select-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
          </label>
        )}
      </div>
    )
  }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
