"use client";

import { useState } from "react";
import { api, PredictionOutput, ProductInput } from "@/lib/api";
import TierBadge from "@/components/TierBadge";

const CATEGORIES  = ["Accessories","Pants","Polo","Shirt","Shoes","Shorts","Sweatshirt","Swimwear","T-Shirt"];
const COLLECTIONS = ["Box Logo","Circular","Cresta","Geographic","Iconic","Morgex","Patch","Rainforest","Slate","Sun-Lover","Trail","Tribe","Wave"];
const SEXES       = ["Men","Women"];
const SEASONS     = ["FS24","SS25","SS26","FS25"];
const ALPHA_SIZES = ["XS","S","M","L","XL","XXL","One Size"];
const NUM_SIZES   = ["36","37","38","39","40","41","42","43","44","45","46"];

const defaultForm: ProductInput = {
  product_category : "T-Shirt",
  collection_family: "Box Logo",
  sex              : "Men",
  color            : "",
  season           : "SS26",
  size             : "M",
  price            : 49.99,
  discount         : 0,
  sell_through     : 0,
};

const tierColors = {
  dead_stock : { bar: "bg-red-500",    text: "text-red-400",    label: "Dead Stock"  },
  average    : { bar: "bg-orange-400", text: "text-orange-400", label: "Average"     },
  fast_mover : { bar: "bg-green-500",  text: "text-green-400",  label: "Fast Mover"  },
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-zinc-400 mb-1 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 transition-colors";

export default function Tester() {
  const [form, setForm]       = useState<ProductInput>(defaultForm);
  const [result, setResult]   = useState<PredictionOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [isShoes, setIsShoes] = useState(false);

  const set = (field: keyof ProductInput, value: string | number) => {
    setForm((f) => {
      const next = { ...f, [field]: value };
      if (field === "product_category") {
        const shoes = value === "Shoes";
        setIsShoes(shoes);
        next.size = shoes ? "42" : "M";
      }
      return next;
    });
  };

  const submit = async () => {
    if (!form.color.trim()) { setError("Color is required"); return; }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const r = await api.predict(form);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const tier = result?.predicted_tier;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Product Tester</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Score any product from a new collection — see its predicted tier, confidence, and recommended action.
          The model fuzzy-matches color and collection names so you can use your own naming.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-300">Product Details</h2>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Category">
              <select className={inputCls} value={form.product_category}
                onChange={(e) => set("product_category", e.target.value)}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Collection">
              <input className={inputCls} value={form.collection_family}
                onChange={(e) => set("collection_family", e.target.value)}
                placeholder="e.g. Rainforest, Wave..." list="collections-list" />
              <datalist id="collections-list">
                {COLLECTIONS.map((c) => <option key={c} value={c} />)}
              </datalist>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Gender">
              <select className={inputCls} value={form.sex} onChange={(e) => set("sex", e.target.value)}>
                {SEXES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Season">
              <select className={inputCls} value={form.season} onChange={(e) => set("season", e.target.value)}>
                {SEASONS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Color (free text — fuzzy matched to training vocabulary)">
            <input className={inputCls} value={form.color}
              onChange={(e) => set("color", e.target.value)}
              placeholder="e.g. Wine Red, Dark Burgundy, Navy Blue..." />
          </Field>

          <Field label="Size">
            <select className={inputCls} value={form.size} onChange={(e) => set("size", e.target.value)}>
              {(isShoes ? NUM_SIZES : ALPHA_SIZES).map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Price (€)">
              <input type="number" className={inputCls} value={form.price} min={1} step={0.01}
                onChange={(e) => set("price", parseFloat(e.target.value))} />
            </Field>
            <Field label="Current Discount (%)">
              <input type="number" className={inputCls} value={form.discount} min={0} max={100}
                onChange={(e) => set("discount", parseFloat(e.target.value))} />
            </Field>
          </div>

          <Field label={`Estimated Sell-Through: ${(form.sell_through * 100).toFixed(0)}%`}>
            <input type="range" className="w-full accent-green-500" min={0} max={1} step={0.01}
              value={form.sell_through} onChange={(e) => set("sell_through", parseFloat(e.target.value))} />
            <div className="flex justify-between text-xs text-zinc-500 mt-1">
              <span>0% (not sold)</span><span>50%</span><span>100% (sold out)</span>
            </div>
          </Field>

          {error && <p className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}

          <button onClick={submit} disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm">
            {loading ? "Predicting..." : "Predict Tier →"}
          </button>
        </div>

        {/* Result */}
        <div className="space-y-4">
          {!result && !loading && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
              <p className="text-zinc-500 text-sm">Fill in the product details and hit Predict.</p>
              <p className="text-zinc-600 text-xs mt-2">
                Use new collection names freely — the model normalizes them automatically.
              </p>
            </div>
          )}

          {loading && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
              <div className="animate-pulse text-green-400 text-sm">Running model...</div>
            </div>
          )}

          {result && tier && (
            <>
              {/* Main result */}
              <div className={`bg-zinc-900 border rounded-xl p-6 ${
                tier === "dead_stock" ? "border-red-500/40" : tier === "fast_mover" ? "border-green-500/40" : "border-orange-400/40"
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <TierBadge tier={tier} />
                  <span className="text-xs text-zinc-400">
                    {(result.confidence * 100).toFixed(1)}% confidence
                  </span>
                </div>
                <p className="text-2xl font-bold text-white mb-1">
                  {result.recommended_discount === 0 ? "No discount needed" : `${result.recommended_discount}% discount`}
                </p>
                <p className="text-sm text-zinc-400">{result.reason}</p>

                {/* Probability bars */}
                <div className="mt-5 space-y-2">
                  {Object.entries(result.probabilities)
                    .sort((a, b) => b[1] - a[1])
                    .map(([t, p]) => {
                      const tc = tierColors[t as keyof typeof tierColors];
                      return (
                        <div key={t}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className={tc.text}>{tc.label}</span>
                            <span className="text-zinc-400">{(p * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 bg-zinc-800 rounded-full">
                            <div className={`h-1.5 ${tc.bar} rounded-full transition-all`} style={{ width: `${p * 100}%` }} />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Normalization warnings */}
              {result.input_normalizations.length > 0 && (
                <div className="bg-zinc-900 border border-orange-400/20 rounded-xl p-4">
                  <p className="text-xs font-semibold text-orange-300 mb-2">
                    ⚡ Input Normalized — {result.input_normalizations.length} field(s) remapped
                  </p>
                  <div className="space-y-1.5">
                    {result.input_normalizations.map((n) => (
                      <div key={n.field} className="text-xs text-zinc-400 flex items-center gap-2">
                        <span className="text-zinc-500 capitalize">{n.field.replace("_", " ")}:</span>
                        <span className="text-orange-300 line-through">{n.original}</span>
                        <span className="text-zinc-500">→</span>
                        <span className="text-green-400">{n.matched}</span>
                        <span className="text-zinc-600">({n.score.toFixed(0)}% match)</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-zinc-600 mt-2">
                    The model mapped your input to the closest known training values. Check these are correct.
                  </p>
                </div>
              )}

              {/* Action summary */}
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-zinc-300 mb-2">Recommended Action</p>
                {tier === "fast_mover" && (
                  <p className="text-xs text-zinc-400">
                    This product is predicted to sell well. <span className="text-green-400 font-medium">Consider including it in the next collection order.</span>{" "}
                    Prioritise restocking if it shares attributes with SS25 fast movers (same collection, category, or color family).
                  </p>
                )}
                {tier === "average" && (
                  <p className="text-xs text-zinc-400">
                    This product sits in the middle — it will sell but won&apos;t fly.{" "}
                    <span className="text-orange-400 font-medium">Order conservatively</span> and use a {result.recommended_discount}% discount as a stimulus if sell-through stalls below 40%.
                  </p>
                )}
                {tier === "dead_stock" && (
                  <p className="text-xs text-zinc-400">
                    High risk of becoming dead stock based on similar products.{" "}
                    <span className="text-red-400 font-medium">Either skip this product or order minimal quantities</span>{" "}
                    and apply a {result.recommended_discount}% entry discount immediately to stimulate early sell-through.
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* How it works */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">How the Model Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-zinc-400">
          <div>
            <p className="text-white font-medium mb-1">Training</p>
            Logistic Regression trained on 1,936 real SKUs from FS24 and SS25.
            SMOTE balanced the classes (683 samples per tier).
            GridSearchCV found C=10, L2 penalty, saga solver.
          </div>
          <div>
            <p className="text-white font-medium mb-1">Threshold</p>
            Dead stock probability threshold tuned to 0.36 (instead of default 0.5).
            This achieves 89% recall on dead stock — the model catches almost every dead stock case,
            at the cost of some false positives in the average class.
          </div>
          <div>
            <p className="text-white font-medium mb-1">Fuzzy Matching</p>
            Color and collection names are fuzzy-matched to the training vocabulary.
            &quot;Wine Red&quot; maps to &quot;Burgundy&quot;, &quot;rainforest collection&quot; maps to &quot;Rainforest&quot;.
            If no match is found (&lt;75% similarity), the value passes through — the model still runs
            but confidence may be lower.
          </div>
        </div>
      </div>
    </div>
  );
}
