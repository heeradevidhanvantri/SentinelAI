import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  default: "bg-primary/20 text-primary border-primary/30",
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  medium: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  low: "bg-green-500/20 text-green-400 border-green-500/30",
  healthy: "bg-green-500/20 text-green-400 border-green-500/30",
  degraded: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

export function Badge({
  className,
  variant = "default",
  children,
}: {
  className?: string;
  variant?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
        variants[variant] || variants.default,
        className
      )}
    >
      {children}
    </span>
  );
}
