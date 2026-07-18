import {
  getFaithfulnessTrend,
  getToxicityBreakdown,
  getModelComparison,
  getTotalEvals,
} from "@/lib/services/evals";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export const dynamic = "force-dynamic";

export default async function EvalsPage() {
  const [faithfulness, toxicity, modelComparison, totalEvals] = await Promise.all([
    getFaithfulnessTrend().catch(() => []),
    getToxicityBreakdown().catch(() => []),
    getModelComparison().catch(() => []),
    getTotalEvals().catch(() => 0),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Evaluations</h1>
        <p className="text-sm text-muted-foreground">
          {totalEvals.toLocaleString()} evals in the last 24 hours
        </p>
      </div>

      {/* Faithfulness Trend */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Faithfulness Trend (30d)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={faithfulness}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="day" stroke="var(--muted-foreground)" fontSize={12} />
            <YAxis stroke="var(--muted-foreground)" fontSize={12} domain={[0, 1]} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--foreground)",
              }}
            />
            <Line type="monotone" dataKey="avg_score" stroke="#22c55e" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Toxicity Breakdown */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Toxicity Breakdown</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={toxicity} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis type="number" stroke="var(--muted-foreground)" fontSize={12} domain={[0, 1]} />
            <YAxis type="category" dataKey="category" stroke="var(--muted-foreground)" fontSize={12} width={120} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--foreground)",
              }}
            />
            <Bar dataKey="score" fill="#ef4444" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Model Comparison Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">Model Comparison</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Faithfulness</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Toxicity</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Relevancy</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Eval Count</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {modelComparison.map((row) => (
              <tr key={row.model} className="hover:bg-muted/50">
                <td className="px-4 py-3 text-sm font-medium text-foreground">{row.model}</td>
                <td className="px-4 py-3 text-sm text-foreground">{Number(row.faithfulness).toFixed(3)}</td>
                <td className="px-4 py-3 text-sm text-foreground">{Number(row.toxicity).toFixed(3)}</td>
                <td className="px-4 py-3 text-sm text-foreground">{Number(row.answer_relevancy).toFixed(3)}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{row.eval_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {modelComparison.length === 0 && (
          <p className="p-8 text-center text-muted-foreground">
            No eval data yet. Run the eval jobs to generate scores.
          </p>
        )}
      </div>
    </div>
  );
}
