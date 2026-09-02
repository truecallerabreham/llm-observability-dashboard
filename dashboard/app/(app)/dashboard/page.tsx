import { KPICard } from "@/components/kpi-card";
import { SpansChart, LatencyChart, CostChart } from "@/components/charts";
import {
  getAllKPIMetrics,
  getSpansTimeSeries,
  getLatencyTimeSeries,
  getCostByModel,
} from "@/lib/services/metrics";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function OverviewPage() {
  const [kpis, spansData, latencyData, costData] = await Promise.all([
    getAllKPIMetrics().catch(() => []),
    getSpansTimeSeries().catch(() => []),
    getLatencyTimeSeries().catch(() => []),
    getCostByModel().catch(() => []),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Real-time LLM observability metrics
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            change={kpi.change}
            unit={kpi.unit}
          />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpansChart
          data={spansData as Record<string, unknown>[]}
          xKey="time"
          yKey="value"
          title="Spans per Minute (24h)"
        />
        <LatencyChart
          data={latencyData as Record<string, unknown>[]}
          xKey="time"
          yKey="value"
          title="P95 Latency (24h)"
        />
      </div>

      <CostChart
        data={costData.map((d) => ({ model: d.model, cost: Number(d.cost.toFixed(6)) }))}
        xKey="model"
        yKey="cost"
        title="Cost by Model (24h)"
        height={250}
      />
    </div>
  );
}
