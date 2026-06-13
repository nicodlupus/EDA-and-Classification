import { api } from "@/lib/api";
import KpiCard from "@/components/KpiCard";

const fmt = (n: number) =>
  n >= 1_000_000 ? `€${(n / 1_000_000).toFixed(1)}M` : `€${(n / 1_000).toFixed(0)}K`;

const roiColor = (s: number) =>
  s >= 0.60 ? "text-green-400" : s >= 0.50 ? "text-orange-400" : s >= 0.40 ? "text-orange-500" : "text-red-400";

const roiBg = (s: number) =>
  s >= 0.60 ? "border-green-500/40 bg-green-500/5" : s >= 0.50 ? "border-orange-400/40 bg-orange-400/5" : "border-red-500/40 bg-red-500/5";

export default async function Collections() {
  const [collections, reorder, abc] = await Promise.all([
    api.collections(),
    api.reorder(),
    api.abc(),
  ]);

  const totalRevenue = collections.reduce((s, c) => s + c.total_revenue_eur, 0);

  // group reorder alerts by collection
  const reorderByCollection = reorder.reduce<Record<string, number>>((acc, r) => {
    acc[r.collection_family] = (acc[r.collection_family] ?? 0) + 1;
    return acc;
  }, {});

  // top 10 ABC class A items
  const topA = abc.filter((i) => i.abc_class === "A").slice(0, 10);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Collections</h1>
        <p className="text-sm text-zinc-400 mt-1">
          ROI scoring across all {collections.length} collections — what to reorder, what to cut, what to watch.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Collections" value={collections.length.toString()} />
        <KpiCard label="Best ROI" value={collections[0].collection_family} accent="green"
          sub={`Score ${collections[0].roi_score.toFixed(3)}`} />
        <KpiCard label="Reorder Alerts" value={reorder.length.toString()} accent="orange"
          sub="fast movers ≤ 30 units" />
        <KpiCard label="Class A SKUs" value={topA.length.toString()} accent="green"
          sub="top 80% of revenue" />
      </div>

      {/* Collection cards */}
      <div>
        <h2 className="text-sm font-semibold text-zinc-300 mb-4">Collection ROI Scorecard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {collections.map((c) => {
            const pct = ((c.total_revenue_eur / totalRevenue) * 100).toFixed(1);
            const alerts = reorderByCollection[c.collection_family] ?? 0;
            return (
              <div key={c.collection_family} className={`border rounded-xl p-4 ${roiBg(c.roi_score)}`}>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="font-semibold text-white">{c.collection_family}</p>
                    <p className="text-xs text-zinc-400">{pct}% of total revenue</p>
                  </div>
                  <span className={`text-xl font-bold ${roiColor(c.roi_score)}`}>
                    {c.roi_score.toFixed(2)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-black/20 rounded-lg p-2 text-center">
                    <p className="text-zinc-400">Revenue</p>
                    <p className="text-white font-medium">{fmt(c.total_revenue_eur)}</p>
                  </div>
                  <div className="bg-black/20 rounded-lg p-2 text-center">
                    <p className="text-zinc-400">Avg ST</p>
                    <p className="text-white font-medium">{(c.avg_sell_through * 100).toFixed(0)}%</p>
                  </div>
                  <div className="bg-black/20 rounded-lg p-2 text-center">
                    <p className="text-zinc-400">SKUs</p>
                    <p className="text-white font-medium">{c.total_skus}</p>
                  </div>
                </div>
                <div className="flex justify-between mt-3 text-xs">
                  <span className="text-green-400">🟢 {c.fast_mover_skus} fast movers</span>
                  <span className="text-red-400">🔴 {c.dead_stock_skus} dead stock</span>
                  {alerts > 0 && <span className="text-orange-400">⚠️ {alerts} reorder</span>}
                </div>
                {/* ST bar */}
                <div className="mt-3">
                  <div className="h-1.5 bg-zinc-800 rounded-full">
                    <div
                      className={`h-1.5 rounded-full ${c.avg_sell_through >= 0.6 ? "bg-green-500" : c.avg_sell_through >= 0.4 ? "bg-orange-400" : "bg-red-500"}`}
                      style={{ width: `${c.avg_sell_through * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Reorder alerts */}
      {reorder.length > 0 && (
        <div className="bg-zinc-900 border border-orange-400/20 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-orange-300 mb-1">
            ⚠️ Reorder Alerts — Fast Movers Running Low
          </h2>
          <p className="text-xs text-zinc-500 mb-4">
            {reorder.length} fast-mover SKUs have ≤ 30 units remaining. Restock before they go out of stock.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-zinc-500 border-b border-zinc-800">
                  {["SKU", "Collection", "Gender", "Color", "Size", "Price", "Units Left", "ST%"].map((h) => (
                    <th key={h} className={`pb-2 font-medium ${h === "SKU" ? "text-left" : "text-right"}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {reorder.slice(0, 20).map((r, i) => (
                  <tr key={i} className="border-b border-zinc-800/40 hover:bg-zinc-800/20">
                    <td className="py-2 font-medium text-white text-xs">{r.name}</td>
                    <td className="py-2 text-right text-zinc-400 text-xs">{r.collection_family}</td>
                    <td className="py-2 text-right text-zinc-400 text-xs">{r.sex}</td>
                    <td className="py-2 text-right text-zinc-400 text-xs">{r.color}</td>
                    <td className="py-2 text-right text-zinc-300 text-xs">{r.size}</td>
                    <td className="py-2 text-right text-zinc-300 text-xs">€{r.price}</td>
                    <td className="py-2 text-right">
                      <span className={`font-bold text-xs ${r.quantity_remaining <= 10 ? "text-red-400" : "text-orange-400"}`}>
                        {r.quantity_remaining}
                      </span>
                    </td>
                    <td className="py-2 text-right text-green-400 text-xs">{(r.sell_through * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Class A top revenue SKUs */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-1">ABC Analysis — Class A SKUs</h2>
        <p className="text-xs text-zinc-500 mb-4">These SKUs generate the top 80% of revenue. Never let them go out of stock.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-zinc-500 border-b border-zinc-800">
                {["#", "SKU", "Category", "Collection", "Gender", "Revenue", "Cumulative%"].map((h) => (
                  <th key={h} className={`pb-2 font-medium ${h === "SKU" || h === "#" ? "text-left" : "text-right"}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {topA.map((item, i) => (
                <tr key={i} className="border-b border-zinc-800/40 hover:bg-zinc-800/20">
                  <td className="py-2 text-zinc-500 text-xs">{i + 1}</td>
                  <td className="py-2 font-medium text-white text-xs">{item.name}</td>
                  <td className="py-2 text-right text-zinc-400 text-xs">{item.product_category}</td>
                  <td className="py-2 text-right text-zinc-400 text-xs">{item.collection_family}</td>
                  <td className="py-2 text-right text-zinc-400 text-xs">{item.sex}</td>
                  <td className="py-2 text-right text-green-400 font-medium text-xs">{fmt(item.revenue_eur)}</td>
                  <td className="py-2 text-right text-zinc-400 text-xs">{item.cumulative_pct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
