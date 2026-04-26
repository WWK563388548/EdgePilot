import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1",
  {
    variants: {
      variant: {
        default: "bg-slate-50 text-slate-700 ring-slate-200",
        success: "bg-teal-50 text-teal-700 ring-teal-200",
        warning: "bg-amber-50 text-amber-700 ring-amber-200",
        destructive: "bg-rose-50 text-rose-700 ring-rose-200"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
);

export type BadgeProps = HTMLAttributes<HTMLSpanElement> &
  VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
