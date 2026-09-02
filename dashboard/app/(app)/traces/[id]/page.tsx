import Link from "next/link";
import { getTraceWaterfall, type Trace, type TraceWaterfall } from "@/lib/services/traces";

export const dynamic = "force-dynamic";

export default async function TraceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const spans: Trace[] = await getTraceWaterfall(id).catch(() => []);

  // Build waterfall: calculate depth from ParentSpanId
  const spanMap = new Map<string, TraceWaterfall>(
    spans.map((s) => [s.SpanId, { ...s, depth: 0, children: [] }])
  );
  const roots: TraceWaterfall[] = [];

  spans.forEach((span) => {
    if (span.ParentSpanId && spanMap.has(span.ParentSpanId)) {
      const parent = spanMap.get(span.ParentSpanId)!;
      spanMap.get(span.SpanId)!.depth = parent.depth + 1;
    } else {
      roots.push(spanMap.get(span.SpanId)!);
    }
  });

  const sortedSpans = Array.from(spanMap.values()).sort(
    (a, b) => a.depth - b.depth || new Date(a.StartTime).getTime() - new Date(b.StartTime).getTime()
  );

  const maxDuration = Math.max(...spans.map((s) => s.DurationMs), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/traces" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to Traces
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-foreground">Trace Detail</h1>
        <p className="text-sm font-mono text-muted-foreground">{id}</p>
      </div>

      {/* Waterfall */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Span Waterfall</h3>
        <div className="space-y-1">
          {sortedSpans.map((span) => {
            const widthPercent = (span.DurationMs / maxDuration) * 100;
            const indent = span.depth * 24;

            return (
              <div key={span.SpanId} className="flex items-center gap-2">
                {/* Label */}
                <div
                  className="flex-shrink-0 w-48 text-xs text-foreground truncate"
                  style={{ paddingLeft: `${indent}px` }}
                >
                  <span className="text-muted-foreground">{"  ".repeat(span.depth)}</span>
                  {span.SpanName}
                </div>

                {/* Bar */}
                <div className="flex-1 h-6 bg-muted rounded relative">
                  <div
                    className={`h-full rounded ${
                      span.StatusCode === "ERROR" ? "bg-red-500" : "bg-primary"
                    }`}
                    style={{ width: `${Math.max(widthPercent, 2)}%` }}
                  />
                </div>

                {/* Duration */}
                <div className="flex-shrink-0 w-20 text-xs text-muted-foreground text-right">
                  {span.DurationMs.toFixed(1)}ms
                </div>
              </div>
            );
          })}
        </div>
        {sortedSpans.length === 0 && (
          <p className="text-center text-muted-foreground py-8">
            No spans found for this trace.
          </p>
        )}
      </div>

      {/* Span Details Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Span Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Duration</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Tokens</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sortedSpans.map((span) => (
              <tr key={span.SpanId} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-sm text-foreground font-mono">{span.SpanName}</td>
                <td className="px-4 py-3 text-sm text-foreground">{span.Provider}</td>
                <td className="px-4 py-3 text-sm text-foreground">{span.Model}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    span.StatusCode === "OK"
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                      : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                  }`}>
                    {span.StatusCode}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{span.DurationMs.toFixed(1)}ms</td>
                <td className="px-4 py-3 text-sm text-foreground">
                  {span.InputTokens}+{span.OutputTokens}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
