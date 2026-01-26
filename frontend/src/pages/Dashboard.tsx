import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

type HoldingRow = {
  holding_id: number;
  quantity: number;
  card: {
    id: number;
    name: string;
  };
};

type PriceRow = {
  card_id: number;
  market: number | null;
};

type GradedRow = {
  id: number;
};

const API_BASE =
  (import.meta as any).env?.VITE_API_URL ?? `${window.location.origin}/api`;

const Dashboard = () => {
  const { notify } = useToast();
  const { token } = useAuth();
  const [holdings, setHoldings] = useState<HoldingRow[]>([]);
  const [prices, setPrices] = useState<Record<number, PriceRow>>({});
  const [gradedCount, setGradedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const totalValue = useMemo(() => {
    return holdings.reduce((sum, holding) => {
      const price = prices[holding.card.id]?.market;
      if (!price) return sum;
      return sum + price * holding.quantity;
    }, 0);
  }, [holdings, prices]);

  const pricedCount = useMemo(() => {
    return holdings.filter((holding) => prices[holding.card.id]?.market).length;
  }, [holdings, prices]);

  const topHoldings = useMemo(() => {
    return holdings
      .map((holding) => {
        const price = prices[holding.card.id]?.market ?? 0;
        return {
          name: holding.card.name,
          value: price * holding.quantity,
        };
      })
      .filter((row) => row.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [holdings, prices]);

  const loadDashboard = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const holdingsResponse = await fetch(`${API_BASE}/holdings/my`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!holdingsResponse.ok) {
        throw new Error(`Failed to load holdings (${holdingsResponse.status})`);
      }
      const holdingsData = (await holdingsResponse.json()) as HoldingRow[];
      setHoldings(holdingsData);

      const gradedResponse = await fetch(`${API_BASE}/graded`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (gradedResponse.ok) {
        const gradedData = (await gradedResponse.json()) as GradedRow[];
        setGradedCount(gradedData.length);
      } else {
        setGradedCount(0);
      }

      if (holdingsData.length) {
        const next: Record<number, PriceRow> = {};
        const ids = holdingsData.map((holding) => holding.card.id);
        const batchSize = 50;
        for (let i = 0; i < ids.length; i += batchSize) {
          const batch = ids.slice(i, i + batchSize);
          const priceResponse = await fetch(`${API_BASE}/cards/prices`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ card_ids: batch, fetch_remote: true }),
          });
          if (!priceResponse.ok) continue;
          const payload = (await priceResponse.json()) as { prices: PriceRow[] };
          payload.prices.forEach((price) => {
            next[price.card_id] = price;
          });
        }
        setPrices(next);
      } else {
        setPrices({});
      }
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <section className="space-y-6">
      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-surface p-5">
          <p className="text-sm text-white/50">Total Value</p>
          <h2 className="mt-4 text-2xl font-semibold text-white">
            {loading ? "Loading..." : `$${totalValue.toFixed(2)}`}
          </h2>
          <p className="mt-2 text-xs text-white/50">
            {pricedCount}/{holdings.length} holdings priced
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-surface p-5">
          <p className="text-sm text-white/50">Holdings vs Graded</p>
          <h2 className="mt-4 text-2xl font-semibold text-white">
            {loading ? "Loading..." : `${holdings.length} / ${gradedCount}`}
          </h2>
          <p className="mt-2 text-xs text-white/50">Holdings / graded items</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-surface p-5">
          <p className="text-sm text-white/50">Tracked Alerts</p>
          <h2 className="mt-4 text-2xl font-semibold text-white">0</h2>
          <p className="mt-2 text-xs text-white/50">Alerts are not configured yet</p>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Portfolio value</h3>
            <p className="text-sm text-white/50">Hourly snapshots and valuation trends</p>
          </div>
          <div className="flex gap-2">
            {[
              "24h",
              "7d",
              "30d",
              "1y",
              "All",
            ].map((range) => (
              <button
                key={range}
                className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60 hover:border-accent/60 hover:text-accent"
                onClick={() =>
                  notify({
                    title: "Chart controls are demo-only",
                    description: `The ${range} range will be available once snapshot data is loaded.`,
                  })
                }
                type="button"
              >
                {range}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-6 h-56 rounded-xl border border-dashed border-white/10 bg-base/40" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-surface p-6">
          <h3 className="text-lg font-semibold">Top holdings</h3>
          <p className="text-sm text-white/50">Highest value cards in your collection</p>
          <ul className="mt-4 space-y-3 text-sm">
            {!topHoldings.length && (
              <li className="rounded-xl bg-base/60 px-4 py-3 text-white/50">
                No priced holdings yet.
              </li>
            )}
            {topHoldings.map((row, idx) => (
              <li
                key={`${row.name}-${idx}`}
                className="flex items-center justify-between rounded-xl bg-base/60 px-4 py-3"
              >
                <span>{row.name}</span>
                <span className="text-accent">${row.value.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-white/10 bg-surface p-6">
          <h3 className="text-lg font-semibold">Alerts</h3>
          <p className="text-sm text-white/50">Price thresholds and big movers</p>
          <div className="mt-4 space-y-3">
            <div className="rounded-xl bg-base/60 px-4 py-3 text-sm text-white/50">
              Alerts are not configured yet.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;
