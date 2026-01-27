import { useEffect, useState } from "react";

const STORAGE_KEY = "pv_accent_color";

const Account = () => {
  const [accent, setAccent] = useState("#3aff7a");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setAccent(stored);
      document.documentElement.style.setProperty("--accent", stored);
    }
  }, []);

  const handleChange = (value: string) => {
    setAccent(value);
    localStorage.setItem(STORAGE_KEY, value);
    document.documentElement.style.setProperty("--accent", value);
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <h2 className="text-xl font-semibold">Account</h2>
        <p className="text-sm text-white/50">Personalize the accent color across the app.</p>
        <div className="mt-4 flex items-center gap-4">
          <input
            className="h-12 w-12 cursor-pointer rounded-full border border-white/20 bg-transparent"
            onChange={(event) => handleChange(event.target.value)}
            type="color"
            value={accent}
          />
          <div>
            <div className="text-sm text-white/70">Accent color</div>
            <div className="text-xs text-white/40">{accent.toUpperCase()}</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Account;
