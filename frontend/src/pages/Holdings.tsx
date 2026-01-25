import { useToast } from "../components/Toast";

const Holdings = () => {
  const { notify } = useToast();

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Holdings</h2>
            <p className="text-sm text-white/50">Track quantities, conditions, and tags</p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 hover:border-accent/60 hover:text-accent"
              onClick={() =>
                notify({
                  title: "CSV import is offline",
                  description: "Start the API server to enable imports.",
                })
              }
              type="button"
            >
              Import CSV
            </button>
            <button
              className="rounded-full border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
              onClick={() =>
                notify({
                  title: "Add holding is unavailable",
                  description: "Connect to a user account to add new holdings.",
                })
              }
              type="button"
            >
              Add Holding
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-4">
        {[
          { name: "Charizard Holo", condition: "NM", qty: 1, tags: "PC" },
          { name: "Pikachu Promo", condition: "LP", qty: 3, tags: "Trade" },
        ].map((item) => (
          <div key={item.name} className="rounded-2xl border border-white/10 bg-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold">{item.name}</h3>
                <p className="text-sm text-white/50">{item.condition} • Qty {item.qty}</p>
              </div>
              <div className="flex gap-2 text-xs">
                <span className="rounded-full bg-accent/20 px-3 py-1 text-accent">{item.tags}</span>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-white/60 hover:border-accent/60 hover:text-accent"
                  onClick={() =>
                    notify({
                      title: "Editing is disabled in demo mode",
                      description: "Sign in as an owner to update this holding.",
                    })
                  }
                  type="button"
                >
                  Edit
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Holdings;
