const styles = {
  dead_stock : "bg-red-500/15 text-red-400 border border-red-500/30",
  average    : "bg-orange-400/15 text-orange-300 border border-orange-400/30",
  fast_mover : "bg-green-500/15 text-green-400 border border-green-500/30",
};

const labels = {
  dead_stock : "Dead Stock",
  average    : "Average",
  fast_mover : "Fast Mover",
};

export default function TierBadge({ tier }: { tier: "dead_stock" | "average" | "fast_mover" }) {
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${styles[tier]}`}>
      {labels[tier]}
    </span>
  );
}
