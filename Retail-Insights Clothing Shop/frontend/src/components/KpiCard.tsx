interface Props {
  label: string;
  value: string;
  sub?: string;
  accent?: "green" | "orange" | "red" | "neutral";
}

const accents = {
  green  : "border-l-green-500 text-green-400",
  orange : "border-l-orange-400 text-orange-400",
  red    : "border-l-red-500 text-red-400",
  neutral: "border-l-white/20 text-white",
};

export default function KpiCard({ label, value, sub, accent = "neutral" }: Props) {
  return (
    <div className={`bg-zinc-900 border border-zinc-800 border-l-4 ${accents[accent]} rounded-xl p-5`}>
      <p className="text-xs uppercase tracking-widest text-zinc-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className={`text-xs mt-1 ${accents[accent].split(" ")[1]}`}>{sub}</p>}
    </div>
  );
}
