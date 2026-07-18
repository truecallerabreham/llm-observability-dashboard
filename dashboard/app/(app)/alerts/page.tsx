import { getActiveAlerts, getAlertHistory } from "@/lib/services/alerts";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  const [activeAlerts, alertHistory] = await Promise.all([
    getActiveAlerts().catch(() => []),
    getAlertHistory().catch(() => []),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Alerts</h1>
        <p className="text-sm text-muted-foreground">
          Active alerts and alert history from Prometheus/Alertmanager
        </p>
      </div>

      {/* Active Alerts */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">
            Active Alerts ({activeAlerts.length})
          </h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Alert Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Severity</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Description</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Started At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {activeAlerts.map((alert, i) => (
              <tr key={`${alert.name}-${i}`} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-sm font-medium text-foreground">{alert.name}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    alert.severity === "critical"
                      ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                  }`}>
                    {alert.severity}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{alert.status}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground max-w-md truncate">
                  {alert.description}
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{alert.startedAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {activeAlerts.length === 0 && (
          <p className="p-8 text-center text-muted-foreground">
            No active alerts. All systems healthy.
          </p>
        )}
      </div>

      {/* Alert History */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">Alert History</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Alert Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Severity</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Fired At</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Resolved At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {alertHistory.map((entry, i) => (
              <tr key={`${entry.name}-${i}`} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-sm font-medium text-foreground">{entry.name}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    entry.severity === "critical"
                      ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                  }`}>
                    {entry.severity}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{entry.status}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{entry.firedAt}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{entry.resolvedAt || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {alertHistory.length === 0 && (
          <p className="p-8 text-center text-muted-foreground">
            No alert history yet.
          </p>
        )}
      </div>
    </div>
  );
}
