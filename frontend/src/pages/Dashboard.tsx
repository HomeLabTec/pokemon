const Dashboard = () => {
  return (
    <section className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        {[
          { label: "Total Value", value: "$42,590" },
          { label: "Raw vs Graded", value: "68% / 32%" },
          { label: "Tracked Alerts", value: "12 active" },
        ].map((card) => (
          <div key={card.label} className="rounded-2xl border border-white/10 bg-surface p-5">
            <p className="text-sm text-white/50">{card.label}</p>
            <h2 className="mt-4 text-2xl font-semibold text-white">{card.value}</h2>
          </div>
        ))}
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
          <h3 className="text-lg font-semibold">Top movers</h3>
          <p className="text-sm text-white/50">Biggest gainers and losers</p>
          <ul className="mt-4 space-y-3 text-sm">
            <li className="flex items-center justify-between rounded-xl bg-base/60 px-4 py-3">
              <span>Charizard Holo</span>
              <span className="text-accent">+12.4%</span>
            </li>
            <li className="flex items-center justify-between rounded-xl bg-base/60 px-4 py-3">
              <span>Umbreon VMAX</span>
              <span className="text-red-400">-6.2%</span>
            </li>
          </ul>
        </div>
        <div className="rounded-2xl border border-white/10 bg-surface p-6">
          <h3 className="text-lg font-semibold">Alerts</h3>
          <p className="text-sm text-white/50">Price thresholds and big movers</p>
          <div className="mt-4 space-y-3">
            <div className="rounded-xl bg-base/60 px-4 py-3 text-sm">
              <p className="text-white">PSA 10 Blastoise crossed $220</p>
              <p className="text-white/50">2 hours ago</p>
            </div>
            <div className="rounded-xl bg-base/60 px-4 py-3 text-sm">
              <p className="text-white">Gengar down 9% in 24h</p>
              <p className="text-white/50">7 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Dashboard;
