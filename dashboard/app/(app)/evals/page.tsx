import {
  getFaithfulnessTrend,
  getToxicityBreakdown,
  getModelComparison,
  getTotalEvals,
} from "@/lib/services/evals";
import { FaithfulnessTrend, ToxicityBreakdown } from "./charts";

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
        <FaithfulnessTrend data={faithfulness} />
      </div>

      {/* Toxicity Breakdown */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Toxicity Breakdown</h3>
        <ToxicityBreakdown data={toxicity} />
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
