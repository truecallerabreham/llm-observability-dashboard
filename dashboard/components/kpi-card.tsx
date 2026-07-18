"use client";

import { clsx } from "clsx";

interface KPICardProps {
  label: string;
  value: string;
  change?: number;
  unit?: string;
}

export function KPICard({ label, value, change = 0, unit }: KPICardProps) {
  const isPositive = change >= 0;

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <p className="text-sm text-muted-foreground">{label}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold text-foreground">{value}</p>
        {unit && <p className="text-sm text-muted-foreground">{unit}</p>}
      </div>
      {change !== 0 && (
        <p
          className={clsx(
            "mt-1 text-xs font-medium",
            isPositive ? "text-green-500" : "text-red-500"
          )}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(1)}% from last hour
        </p>
      )}
    </div>
  );
}
