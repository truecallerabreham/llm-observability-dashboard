import { getPSITrend, getDriftEvents, getLatestPSI } from "@/lib/services/drift";
import { PSIChart } from "@/components/charts";

export const dynamic = "force-dynamic";

export default async function DriftPage() {
  const [psiTrend, driftEvents, latestPSI] = await Promise.all([
    getPSITrend().catch(() => []),
    getDriftEvents().catch(() => []),
    getLatestPSI().catch(() => null),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Drift Detection</h1>
        <p className="text-sm text-muted-foreground">
          Prompt distribution drift monitoring via PSI/KL divergence
        </p>
      </div>

      {/* Latest PSI */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-border bg-card p-6">
          <p className="text-sm text-muted-foreground">Latest PSI Score</p>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {latestPSI ? latestPSI.score.toFixed(4) : "N/A"}
          </p>
          {latestPSI && (
            <p className="mt-1 text-xs text-muted-foreground">
              as of {latestPSI.date}
            </p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <p className="text-sm text-muted-foreground">Warning Threshold</p>
          <p className="mt-2 text-3xl font-bold text-yellow-500">0.20</p>
          <p className="mt-1 text-xs text-muted-foreground">PSI &gt; 0.2 = investigate</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <p className="text-sm text-muted-foreground">Critical Threshold</p>
          <p className="mt-2 text-3xl font-bold text-red-500">0.25</p>
          <p className="mt-1 text-xs text-muted-foreground">PSI &gt; 0.25 = immediate action</p>
        </div>
      </div>

      {/* PSI Chart */}
      <PSIChart
        data={psiTrend.map((d) => ({ date: d.date, avg_score: Number(d.avg_score) }))}
        xKey="date"
        yKey="avg_score"
        title="PSI Over Time (90d)"
        height={350}
      />

      {/* Drift Events Log */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">Drift Events (PSI &gt; 0.2)</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">PSI Value</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Alert Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {driftEvents.map((event) => (
              <tr key={event.date} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-sm text-foreground">{event.date}</td>
                <td className="px-4 py-3 text-sm text-foreground">{Number(event.psi_value).toFixed(4)}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    event.alert_level === "critical"
                      ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                  }`}>
                    {event.alert_level}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {driftEvents.length === 0 && (
          <p className="p-8 text-center text-muted-foreground">
            No drift events detected. All distributions are within normal ranges.
          </p>
        )}
      </div>
    </div>
  );
}
