import { useEffect, useMemo, useRef, useState } from "react";
import Chart from "chart.js/auto";

type PricePoint = {
  ts: string;
  market: number | null;
};

type PriceHistoryChartProps = {
  data: PricePoint[];
  label: string;
};

const PriceHistoryChart = ({ data, label }: PriceHistoryChartProps) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<Chart | null>(null);
  const [range, setRange] = useState("1M");

  const chartData = useMemo(() => {
    const points = (data || [])
      .filter((point) => point.market !== null && point.market !== undefined)
      .map((point) => ({
        ts: point.ts,
        market: Number(point.market),
      }))
      .sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
    const deduped = new Map<string, number>();
    points.forEach((point) => {
      const day = new Date(point.ts);
      day.setHours(0, 0, 0, 0);
      deduped.set(day.toISOString(), point.market);
    });
    const entries = Array.from(deduped.entries()).map(([ts, market]) => ({ ts, market }));
    const cutoff = (() => {
      const now = new Date();
      const map: Record<string, number> = {
        "1D": 1,
        "7D": 7,
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365,
      };
      if (range === "ALL") return null;
      const days = map[range] ?? 30;
      const cutoff = new Date(now);
      cutoff.setDate(now.getDate() - days);
      return cutoff.getTime();
    })();
    const filtered = entries.filter((point) => {
      const ts = new Date(point.ts).getTime();
      return cutoff ? ts >= cutoff : true;
    });
    return {
      labels: filtered.map((point) => new Date(point.ts).toLocaleDateString()),
      values: filtered.map((point) => point.market),
    };
  }, [data, range]);

  const accent = useMemo(() => {
    if (typeof window === "undefined") return "#f59e0b";
    return getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#f59e0b";
  }, [range]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, ctx.canvas.width, 0);
    gradient.addColorStop(0, accent || "#f59e0b");
    gradient.addColorStop(1, "rgba(245, 158, 11, 0.6)");

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label,
            data: chartData.values,
            borderColor: gradient,
            borderWidth: 2.5,
            backgroundColor: "rgba(245, 158, 11, 0.25)",
            tension: 0.4,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              callback: (value) => `$${value}`,
            },
            grid: {
              color: "rgba(255,255,255,0.08)",
            },
          },
          x: {
            grid: {
              color: "rgba(255,255,255,0.05)",
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: (context) => `$${context.parsed.y}`,
            },
          },
        },
      },
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [chartData.labels, chartData.values, label, accent]);

  if (!chartData.values.length) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border border-white/10 bg-base/40 text-sm text-white/50">
        No price history yet.
      </div>
    );
  }

  return (
    <div className="w-full space-y-3 rounded-xl border border-white/10 bg-base/40 p-3">
      <div className="flex flex-wrap gap-2">
        {["1D", "7D", "1M", "3M", "6M", "1Y", "ALL"].map((option) => (
          <button
            key={option}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              range === option
                ? "bg-accent text-black"
                : "border border-white/10 text-white/70 hover:border-accent/60 hover:text-accent"
            }`}
            onClick={() => setRange(option)}
            type="button"
          >
            {option === "ALL" ? "All" : option}
          </button>
        ))}
      </div>
      <div className="h-48">
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
};

export type { PricePoint };
export default PriceHistoryChart;
