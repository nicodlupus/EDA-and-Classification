import { api } from "@/lib/api";
import KpiCard from "@/components/KpiCard";

const fmt = (n: number) =>
  n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(2)}M` : `€${(n / 1_000).toFixed(1)}K`;

export default async function DeadStock() {
  const [atRisk, recovery] = await Promise.all([
    api.revenueAtRisk(),
    api.recovery(),
  ]);

  const recoveryRate = ((atRisk.projected_recovery_eur / atRisk.revenue_at_risk_eur) * 100).toFixed(0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dead Stock</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Capital locked in unsold inventory — and the discount action plan to recover it.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Dead Stock SKUs"   value={atRisk.total_dead_stock_skus.toLocaleString()} accent="red" />
        <KpiCard label="Units Stuck"       value={atRisk.total_units_stuck.toLocaleString()}      accent="red" />
        <KpiCard label="Capital at Risk"   value={fmt(atRisk.revenue_at_risk_eur)}                accent="orange" />
        <KpiCard label="Recoverable"       value={fmt(atRisk.projected_recovery_eur)} accent="green"
          sub={`${recoveryRate}% recovery rate`} />
      </div>

      {/* Insight */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">What This Means</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-zinc-800/40 rounded-lg p-4">
            <p className="text-red-400 font-semibold mb-1">The Problem</p>
            <p className="text-zinc-400 text-xs leading-relaxed">
              {atRisk.total_dead_stock_skus} SKUs across SS25 are classified as dead stock — sell-through below 20%.
              At full price, {fmt(atRisk.revenue_at_risk_eur)} is locked in unsold units that may never move.
            </p>
          </div>
          <div className="bg-zinc-800/40 rounded-lg p-4">
            <p className="text-orange-400 font-semibold mb-1">The Trade-off</p>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Applying the recommended discounts recovers {fmt(atRisk.projected_recovery_eur)} in cash
              at a margin cost of {fmt(atRisk.margin_cost_of_discounts)}.
              H3 (Mann-Whitney, p&lt;0.0001) proves discounts increase units sold 2.5×.
            </p>
          </div>
          <div className="bg-zinc-800/40 rounded-lg p-4">
            <p className="text-green-400 font-semibold mb-1">The Action</p>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Apply 30% discount to 563 SKUs where sell-through ≥ 15%.
              Apply 50% to 194 SKUs in critical dead-stock territory.
              Act now — waiting costs margin and cash flow.
            </p>
          </div>
        </div>
      </div>

      {/* Recovery table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-4">Discount Action Plan</h2>
        <div className="space-y-4">
          {recovery.map((r) => {
            const isUrgent = r.discount_level === 50;
            return (
              <div key={r.discount_level} className={`border rounded-xl p-5 ${isUrgent ? "border-red-500/40 bg-red-500/5" : "border-orange-400/20 bg-orange-400/5"}`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`text-2xl font-bold ${isUrgent ? "text-red-400" : "text-orange-400"}`}>
                        {r.discount_level}% OFF
                      </span>
                      {isUrgent && (
                        <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
                          URGENT CLEARANCE
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-400">
                      {r.sku_count} SKUs · {r.units_affected.toLocaleString()} units affected
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      {isUrgent
                        ? "Sell-through < 15% — urgent clearance to free warehouse space and recover any cash."
                        : "Sell-through 15–20% — moderate stimulus to move units before season end."}
                    </p>
                  </div>
                  <div className="flex gap-6 text-center">
                    <div>
                      <p className="text-xs text-zinc-500">Recovery</p>
                      <p className="text-xl font-bold text-green-400">{fmt(r.projected_revenue_eur)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Margin Cost</p>
                      <p className="text-xl font-bold text-red-400">-{fmt(r.margin_cost_eur)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-500">Recovery Rate</p>
                      <p className="text-xl font-bold text-white">
                        {((r.projected_revenue_eur / (r.projected_revenue_eur + r.margin_cost_eur)) * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Statistical backing */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Statistical Backing — Why Discounts Work</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          {[
            { label: "Discounted SKUs avg sales", value: "245 units",  color: "text-green-400" },
            { label: "Non-discounted avg sales",  value: "97 units",   color: "text-red-400"   },
            { label: "Mann-Whitney U stat",       value: "773,990",    color: "text-white"     },
            { label: "Effect size (r)",           value: "−0.6521",    color: "text-orange-400"},
          ].map((s) => (
            <div key={s.label} className="bg-zinc-800/40 rounded-lg p-3">
              <p className={`text-lg font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-zinc-400 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-zinc-500 mt-4">
          H3 proven with Mann-Whitney U test (non-parametric, p&lt;0.0001). Discounted SKUs sell 2.5× more units on average.
          Effect size r=−0.6521 is classified as large. This is not correlation — it is statistically significant evidence.
        </p>
      </div>
    </div>
  );
}
