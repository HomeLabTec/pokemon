const steps = [
  {
    title: "Import catalog",
    description: "Load full English dataset into PostgreSQL.",
  },
  {
    title: "Download images",
    description: "Prefetch official scans and store locally.",
  },
  {
    title: "Seed prices",
    description: "Fetch initial market prices for tracked cards.",
  },
  {
    title: "Invite friends",
    description: "Create users and share collections.",
  },
];

const Admin = () => {
  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <h2 className="text-xl font-semibold">Setup Wizard</h2>
        <p className="text-sm text-white/50">Complete initial bootstrap tasks to go offline-ready.</p>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {steps.map((step, idx) => (
            <div key={step.title} className="rounded-2xl border border-white/10 bg-base/60 p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Step {idx + 1}: {step.title}</h3>
                <button className="rounded-full border border-accent/40 px-3 py-1 text-xs text-accent hover:bg-accent/10">
                  Run
                </button>
              </div>
              <p className="mt-2 text-sm text-white/50">{step.description}</p>
              <div className="mt-4 h-2 rounded-full bg-white/10">
                <div className="h-2 w-1/3 rounded-full bg-accent" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <h3 className="text-lg font-semibold">Job runs</h3>
        <div className="mt-4 space-y-3 text-sm">
          <div className="flex items-center justify-between rounded-xl bg-base/60 px-4 py-3">
            <span>Catalog import</span>
            <span className="text-white/50">Last run: 2 hours ago</span>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-base/60 px-4 py-3">
            <span>Image prefetch</span>
            <span className="text-white/50">Queued</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Admin;
