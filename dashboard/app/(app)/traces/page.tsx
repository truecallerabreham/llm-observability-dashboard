import Link from "next/link";
import { searchTraces, getAvailableModels, getAvailableProviders } from "@/lib/services/traces";

export const dynamic = "force-dynamic";

export default async function TracesPage() {
  const [traces, models, providers] = await Promise.all([
    searchTraces({ limit: 50 }).catch(() => []),
    getAvailableModels().catch(() => []),
    getAvailableProviders().catch(() => []),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Traces</h1>
        <p className="text-sm text-muted-foreground">
          Search and explore LLM request traces
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select className="px-3 py-2 rounded-lg border border-border bg-card text-sm text-foreground">
          <option value="">All Models</option>
          {models.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <select className="px-3 py-2 rounded-lg border border-border bg-card text-sm text-foreground">
          <option value="">All Providers</option>
          {providers.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select className="px-3 py-2 rounded-lg border border-border bg-card text-sm text-foreground">
          <option value="">All Status</option>
          <option value="OK">OK</option>
          <option value="ERROR">Error</option>
        </select>
      </div>

      {/* Traces Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Trace ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Provider</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Model</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Duration</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tokens</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {traces.map((trace) => (
              <tr key={trace.TraceId + trace.SpanId} className="hover:bg-muted/50 transition-colors">
                <td className="px-4 py-3">
                  <Link
                    href={`/traces/${trace.TraceId}`}
                    className="text-sm font-mono text-primary hover:underline"
                  >
                    {trace.TraceId.slice(0, 12)}...
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{trace.Provider}</td>
                <td className="px-4 py-3 text-sm text-foreground">{trace.Model}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      trace.StatusCode === "OK"
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                        : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                    }`}
                  >
                    {trace.StatusCode}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{trace.DurationMs.toFixed(0)}ms</td>
                <td className="px-4 py-3 text-sm text-foreground">
                  {trace.InputTokens}+{trace.OutputTokens}
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{trace.StartTime}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {traces.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            No traces found. Run the SDK clients to generate traces.
          </div>
        )}
      </div>
    </div>
  );
}
