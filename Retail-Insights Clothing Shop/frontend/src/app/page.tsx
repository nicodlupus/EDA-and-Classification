import { api } from "@/lib/api";
import KpiCard from "@/components/KpiCard";

const fmt = (n: number) =>
  n >= 1_000_000
    ? `€${(n / 1_000_000).toFixed(1)}M`
    : n >= 1_000
    ? `€${(n / 1_000).toFixed(0)}K`
    : `€${n.toFixed(0)}`;

export default async function Overview() {
  const [summary, atRisk, recovery, seasons, collections] = await Promise.all([
    api.summary(),
    api.revenueAtRisk(),
    api.recovery(),
    api.seasons(),
    api.collections(),
  ]);

  const avg_skus = summary.total_skus - summary.dead_stock_skus - summary.fast_mover_skus;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Overview</h1>
        <p className="text-sm text-zinc-400 mt-1">
          1,936 SKUs scored by the ML model · SS25 &amp; FS24 seasons
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KpiCard label="Total SKUs"       value={summary.total_skus.toLocaleString()} accent="neutral" />
        <KpiCard label="Revenue Sold"     value={fmt(summary.total_revenue_eur)}       accent="green"   />
        <KpiCard label="Avg Sell-Through" value={`${(summary.avg_sell_through * 100).toFixed(1)}%`} />
        <KpiCard label="Fast Movers"      value={summary.fast_mover_skus.toString()}   accent="green"   />
        <KpiCard label="Dead Stock SKUs"  value={summary.dead_stock_skus.toString()}   accent="red"     />
        <KpiCard label="Capital at Risk"  value={fmt(summary.revenue_at_risk)} accent="orange"
          sub={`${fmt(atRisk.projected_recovery_eur)} recoverable`} />
      </div>

      {/* Tier + Season */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tier breakdown */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-zinc-300 mb-4">Inventory Tier Split</h2>
          <div className="space-y-3">
            {[
              { label: "Fast Mover", count: summary.fast_mover_skus, color: "bg-green-500",  pct: summary.fast_mover_skus / summary.total_skus },
              { label: "Average",    count: avg_skus,                 color: "bg-orange-400", pct: avg_skus / summary.total_skus                 },
              { label: "Dead Stock", count: summary.dead_stock_skus,  color: "bg-red-500",    pct: summary.dead_stock_skus / summary.total_skus  },
            ].map((t) => (
              <div key={t.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-zinc-300">{t.label}</span>
                  <span className="text-zinc-400">{t.count} SKUs · {(t.pct * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full">
                  <div className={`h-2 ${t.color} rounded-full`} style={{ width: `${t.pct * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Season cards */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          {seasons.map((s) => (
            <div key={s.season} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
              <p className="text-xs text-zinc-400 uppercase tracking-widest mb-2">{s.season}</p>
              <p className="text-2xl font-bold text-white">{fmt(s.revenue_eur)}</p>
              <p className="text-sm text-zinc-400 mt-1">{(s.avg_sell_through * 100).toFixed(0)}% sell-through</p>
              <p className="text-xs text-zinc-500">{s.units_sold.toLocaleString()} units sold</p>
              <div className="flex gap-4 mt-3 text-xs">
                <span className="text-green-400 font-medium">🟢 {s.fast_mover_skus} fast movers</span>
                <span className="text-red-400 font-medium">🔴 {s.dead_stock_skus} dead stock</span>
              </div>
            </div>
          ))}
          <div className="col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <p className="text-xs text-zinc-500">
              <span className="text-orange-400 font-medium">Why two seasons?</span>{" "}
              FS24 is a mature season — fully sold through, no dead stock. SS25 is the current season —
              lower velocity, 757 SKUs flagged for discount action before they become permanent dead stock.
              The model learns from FS24 patterns to predict SS25 outcomes.
            </p>
          </div>
        </div>
      </div>

      {/* Dead stock recovery */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-1">Dead Stock Recovery Plan</h2>
        <p className="text-xs text-zinc-500 mb-5">
          {atRisk.total_units_stuck.toLocaleString()} units stuck ·{" "}
          {fmt(atRisk.revenue_at_risk_eur)} at risk ·{" "}
          {fmt(atRisk.projected_recovery_eur)} recoverable with targeted discounts
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {recovery.map((r) => (
            <div key={r.discount_level} className="flex items-center justify-between bg-zinc-800/40 rounded-lg px-4 py-3">
              <div>
                <span className="text-white font-semibold">{r.discount_level}% discount</span>
                <p className="text-zinc-400 text-xs mt-0.5">{r.sku_count} SKUs · {r.units_affected.toLocaleString()} units</p>
              </div>
              <div className="text-right">
                <p className="text-green-400 font-medium">{fmt(r.projected_revenue_eur)}</p>
                <p className="text-red-400 text-xs">-{fmt(r.margin_cost_eur)} margin cost</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Collection table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-4">Collections by ROI Score</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-zinc-500 border-b border-zinc-800">
                {["Collection", "Revenue", "Avg ST%", "Fast Movers", "Dead Stock", "ROI Score"].map((h) => (
                  <th key={h} className={`pb-2 font-medium ${h === "Collection" ? "text-left" : "text-right"}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {collections.map((c) => (
                <tr key={c.collection_family} className="border-b border-zinc-800/40 hover:bg-zinc-800/20 transition-colors">
                  <td className="py-2.5 font-medium text-white">{c.collection_family}</td>
                  <td className="py-2.5 text-right text-zinc-300">{fmt(c.total_revenue_eur)}</td>
                  <td className="py-2.5 text-right text-zinc-300">{(c.avg_sell_through * 100).toFixed(0)}%</td>
                  <td className="py-2.5 text-right text-green-400">{c.fast_mover_skus}</td>
                  <td className="py-2.5 text-right text-red-400">{c.dead_stock_skus}</td>
                  <td className="py-2.5 text-right">
                    <span className={`font-bold ${c.roi_score >= 0.55 ? "text-green-400" : c.roi_score >= 0.45 ? "text-orange-400" : "text-red-400"}`}>
                      {c.roi_score.toFixed(3)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
