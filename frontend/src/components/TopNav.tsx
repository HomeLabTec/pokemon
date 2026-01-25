import { useAuth } from "../auth/AuthContext";
import { useToast } from "./Toast";

const TopNav = () => {
  const { notify } = useToast();
  const { user, logout } = useAuth();
  const initials = user?.name
    ? user.name
        .split(" ")
        .map((part) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "UA";

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
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-white/50">Signed in</p>
              <p className="text-sm text-white">{user?.email ?? "Unknown"}</p>
            </div>
            <button
              aria-label="User account menu"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent hover:bg-accent/30"
              type="button"
            >
              {initials}
            </button>
            <button
              className="rounded-full border border-white/10 px-3 py-2 text-xs text-white/70 hover:bg-white/10"
              onClick={logout}
              type="button"
            >
              Log out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
