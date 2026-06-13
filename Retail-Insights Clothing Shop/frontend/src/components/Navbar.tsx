"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/",            label: "Overview"    },
  { href: "/collections", label: "Collections" },
  { href: "/dead-stock",  label: "Dead Stock"  },
  { href: "/tester",      label: "Tester"      },
];

export default function Navbar() {
  const path = usePathname();
  return (
    <nav className="sticky top-0 z-50 bg-black/80 backdrop-blur border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-6 flex items-center gap-8 h-14">
        <span className="text-white font-bold tracking-tight text-sm">
          RETAIL <span className="text-green-400">INSIGHTS</span>
        </span>
        <div className="flex gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                path === l.href
                  ? "bg-green-500/20 text-green-400"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
