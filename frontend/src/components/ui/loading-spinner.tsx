import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function LoadingSpinner({
  label = "Loading...",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center gap-3 text-muted-foreground", className)}>
      <Loader2 className="h-8 w-8 animate-spin text-sentinel-cyan" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
