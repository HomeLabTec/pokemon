import { useToast } from "./Toast";

const TopNav = () => {
  const { notify } = useToast();

  return (
    <header className="sticky top-0 z-50 bg-surface/90 backdrop-blur border-b border-white/10">
      <div className="mx-auto flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-2xl font-semibold text-accent">PokeVault</h1>
          <p className="text-sm text-white/60">Private Pokémon collection + valuation</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            className="rounded-full border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
            onClick={() =>
              notify({
                title: "Sync status is demo-only",
                description: "Run the backend jobs to enable real sync activity.",
              })
            }
            type="button"
          >
            Sync status
          </button>
          <button
            aria-label="User account menu"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent hover:bg-accent/30"
            onClick={() =>
              notify({
                title: "Account menu unavailable",
                description: "Create a user in the admin panel to enable account switching.",
              })
            }
            type="button"
          >
            UA
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
