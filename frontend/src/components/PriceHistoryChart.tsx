import { useEffect, useMemo, useRef } from "react";
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

  const chartData = useMemo(() => {
    const points = (data || [])
      .filter((point) => point.market !== null && point.market !== undefined)
      .map((point) => ({
        ts: point.ts,
        market: Number(point.market),
      }))
      .sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
    return {
      labels: points.map((point) => new Date(point.ts).toLocaleDateString()),
      values: points.map((point) => point.market),
    };
  }, [data]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label,
            data: chartData.values,
            borderColor: "#f97316",
            backgroundColor: "rgba(249, 115, 22, 0.2)",
            tension: 0.3,
            fill: true,
            pointRadius: 2,
            pointHoverRadius: 4,
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
              color: "rgba(255,255,255,0.06)",
            },
          },
          x: {
            grid: {
              color: "rgba(255,255,255,0.04)",
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
  }, [chartData.labels, chartData.values, label]);

  if (!chartData.values.length) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border border-white/10 bg-base/40 text-sm text-white/50">
        No price history yet.
      </div>
    );
  }

  return (
    <div className="h-48 w-full rounded-xl border border-white/10 bg-base/40 p-3">
      <canvas ref={canvasRef} />
    </div>
  );
};

export type { PricePoint };
export default PriceHistoryChart;
