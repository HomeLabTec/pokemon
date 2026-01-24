const Catalog = () => {
  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Card Catalog</h2>
            <p className="text-sm text-white/50">Search sets, types, rarities, and variants</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              className="w-56 rounded-full bg-base/60 px-4 py-2 text-sm text-white/70 placeholder:text-white/30"
              placeholder="Search cards"
            />
            <button className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 hover:border-accent/60 hover:text-accent">
              Filters
            </button>
            <button className="rounded-full border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10">
              Save View
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, idx) => (
          <div key={idx} className="rounded-2xl border border-white/10 bg-surface p-4">
            <div className="aspect-[3/4] rounded-xl bg-base/50" />
            <div className="mt-4">
              <h3 className="text-sm font-semibold">Sample Card #{idx + 1}</h3>
              <p className="text-xs text-white/50">Sword & Shield • Rare</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-accent">$128.40</span>
                <span className="text-white/40">Owned: 2</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Catalog;
