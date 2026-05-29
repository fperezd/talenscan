import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100",
        className
      )}
    />
  );
}

export function SkeletonList({ rows = 3, rowClassName }: { rows?: number; rowClassName?: string }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className={cn(
            "rounded-xl border border-slate-200 bg-white p-4",
            rowClassName
          )}
        >
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="mt-2 h-3 w-1/3" />
          <Skeleton className="mt-3 h-3 w-1/4" />
        </div>
      ))}
    </div>
  );
}
