import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import CardDetailModal from "../components/CardDetailModal";
import { useToast } from "../components/Toast";
import HoldingModal, {
  buildHoldingNotes,
  parseHoldingNotes,
  HoldingDraft,
} from "../components/HoldingModal";
import GradedValueModal, { GradedRequest } from "../components/GradedValueModal";
import type { PricePoint } from "../components/PriceHistoryChart";

type HoldingRow = {
  holding_id: number;
  quantity: number;
  condition: string;
  is_for_trade: boolean;
  is_wantlist: boolean;
  is_watched: boolean;
  notes?: string | null;
  card: {
    id: number;
    name: string;
    number: string;
    rarity?: string | null;
  };
  set: {
    id: number;
    code: string;
    name: string;
  };
};

type GradedRow = {
  id: number;
  card_id: number;
  grader: string;
  grade: string;
};

type CardImageRow = {
  kind: string;
  local_path?: string | null;
};

type CardDetail = {
  images: CardImageRow[];
  card?: {
    supertype?: string | null;
    subtypes?: string[] | null;
    types?: string[] | null;
    hp?: string | null;
    artist?: string | null;
  };
  price_history?: PricePoint[];
  latest_prices?: { market: number | null }[];
};

const API_BASE =
  (import.meta as any).env?.VITE_API_URL ?? `${window.location.origin}/api`;

const Holdings = () => {
  const { notify } = useToast();
  const { token } = useAuth();
  const [holdings, setHoldings] = useState<HoldingRow[]>([]);
  const [sets, setSets] = useState<{ id: number; name: string }[]>([]);
  const [selectedSetId, setSelectedSetId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("value");
  const [cardSize, setCardSize] = useState(200);
  const [imageMap, setImageMap] = useState<Record<number, string>>({});
  const [priceMap, setPriceMap] = useState<Record<number, { market: number | null }>>({});
  const [gradedMap, setGradedMap] = useState<Record<number, GradedRow>>({});
  const [gradedPrices, setGradedPrices] = useState<Record<number, { market: number | null }>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<HoldingRow | null>(null);
  const [saving, setSaving] = useState(false);
  const [gradingCard, setGradingCard] = useState<HoldingRow | null>(null);
  const [gradedCooldowns, setGradedCooldowns] = useState<Record<number, number>>({});
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailImage, setDetailImage] = useState("");
  const [detailHistory, setDetailHistory] = useState<PricePoint[]>([]);
  const [detailLatest, setDetailLatest] = useState<number | null>(null);
  const [detailMeta, setDetailMeta] = useState<{
    name?: string;
    number?: string;
    rarity?: string | null;
    setName?: string;
    supertype?: string | null;
    subtypes?: string[] | null;
    types?: string[] | null;
    hp?: string | null;
    artist?: string | null;
    condition?: string;
    quantity?: number;
    grader?: string;
    grade?: string;
    gradedId?: number;
  } | null>(null);

  const loadHoldings = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/holdings/my`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error(`Failed to load holdings (${response.status})`);
      }
      const data = (await response.json()) as HoldingRow[];
      setHoldings(data);
      const cardIds = data.slice(0, 24).map((row) => row.card.id);
      if (cardIds.length) {
        await fetchCardImages(cardIds);
      } else {
        setImageMap({});
      }
      await loadGraded();
    } catch (err: any) {
      setError(err.message || "Failed to load holdings");
    } finally {
      setLoading(false);
    }
  };

  const fetchCardPrices = async (cardIds: number[]) => {
    if (!token) return;
    try {
      const next: Record<number, { market: number | null }> = {};
      const batchSize = 50;
      for (let i = 0; i < cardIds.length; i += batchSize) {
        const batch = cardIds.slice(i, i + batchSize);
        const response = await fetch(`${API_BASE}/cards/prices`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ card_ids: batch, fetch_remote: true }),
        });
        if (!response.ok) {
          continue;
        }
        const payload = (await response.json()) as { prices: { card_id: number; market: number | null }[] };
        payload.prices.forEach((price) => {
          next[price.card_id] = { market: price.market };
        });
      }
      setPriceMap(next);
    } catch {
      setPriceMap({});
    }
  };

  const fetchCardImages = async (cardIds: number[]) => {
    if (!token) return;
    try {
      const results = await Promise.all(
        cardIds.map(async (cardId) => {
          const response = await fetch(`${API_BASE}/cards/${cardId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!response.ok) {
            return { cardId, image: null };
          }
          const detail = (await response.json()) as { images: { kind: string; local_path?: string | null }[] };
          const localImage = detail.images.find((img) => img.kind === "small" && img.local_path)?.local_path;
          return { cardId, image: localImage || null };
        })
      );
      const nextMap: Record<number, string> = {};
      results.forEach((item) => {
        if (item.image) {
          nextMap[item.cardId] = item.image;
        }
      });
      setImageMap(nextMap);
    } catch {
      setImageMap({});
    }
  };

  const openCardDetail = async (item: HoldingRow) => {
    if (!token) return;
    const localImage = imageMap[item.card.id];
    const imageUrl = localImage
      ? `${window.location.origin}${localImage}`
      : `https://images.pokemontcg.io/${item.set.code}/${item.card.number}.png`;
    setDetailImage(imageUrl);
    setDetailOpen(true);
    setDetailHistory([]);
    setDetailLatest(priceMap[item.card.id]?.market ?? null);
    const graded = gradedMap[item.card.id];
    setDetailMeta({
      name: item.card.name,
      number: item.card.number,
      rarity: item.card.rarity ?? null,
      setName: item.set.name,
      condition: item.condition,
      quantity: item.quantity,
      grader: graded?.grader,
      grade: graded?.grade,
      gradedId: graded?.id,
    });
    try {
      const response = await fetch(`${API_BASE}/cards/${item.card.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const detail = (await response.json()) as CardDetail;
        const localLarge = detail.images.find((img) => img.kind === "large" && img.local_path)?.local_path;
        if (localLarge) {
          setDetailImage(`${window.location.origin}${localLarge}`);
        }
        setDetailLatest(detail.latest_prices?.[0]?.market ?? priceMap[item.card.id]?.market ?? null);
        setDetailMeta((prev) => ({
          ...prev,
          supertype: detail.card?.supertype ?? null,
          subtypes: detail.card?.subtypes ?? null,
          types: detail.card?.types ?? null,
          hp: detail.card?.hp ?? null,
          artist: detail.card?.artist ?? null,
        }));
        if (!graded) {
          setDetailHistory(detail.price_history ?? []);
        }
      }
      if (graded) {
        const gradedResponse = await fetch(`${API_BASE}/graded/${graded.id}/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (gradedResponse.ok) {
          const gradedPayload = (await gradedResponse.json()) as { price_history: PricePoint[] };
          setDetailHistory(gradedPayload.price_history ?? []);
        }
      }
    } catch {
      // ignore detail errors
    }
  };

  const loadSets = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/sets`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        return;
      }
      const data = (await response.json()) as { id: number; name: string }[];
      setSets(data);
    } catch {
      setSets([]);
    }
  };

  const loadGraded = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/graded`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        setGradedMap({});
        return;
      }
      const data = (await response.json()) as GradedRow[];
      const map: Record<number, GradedRow> = {};
      data.forEach((row) => {
        map[row.card_id] = row;
      });
      setGradedMap(map);
      const ids = data.map((row) => row.id);
      if (ids.length) {
        await fetchGradedPrices(ids);
      } else {
        setGradedPrices({});
      }
    } catch {
      setGradedMap({});
      setGradedPrices({});
    }
  };

  const fetchGradedPrices = async (gradedIds: number[]) => {
    if (!token) return;
    try {
      const next: Record<number, { market: number | null }> = {};
      const batchSize = 50;
      for (let i = 0; i < gradedIds.length; i += batchSize) {
        const batch = gradedIds.slice(i, i + batchSize);
        const response = await fetch(`${API_BASE}/graded/prices`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ graded_ids: batch, fetch_remote: true }),
        });
        if (!response.ok) continue;
        const payload = (await response.json()) as { prices: { graded_id: number; market: number | null }[] };
        payload.prices.forEach((price) => {
          next[price.graded_id] = { market: price.market };
        });
      }
      setGradedPrices(next);
    } catch {
      setGradedPrices({});
    }
  };

  const saveHolding = async (draft: HoldingDraft) => {
    if (!token || !editing) return;
    setSaving(true);
    try {
      const notes = buildHoldingNotes(draft.meta, draft.notes);
      const response = await fetch(`${API_BASE}/holdings/${editing.holding_id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          quantity: draft.quantity,
          condition: draft.condition,
          is_for_trade: draft.is_for_trade,
          is_wantlist: draft.is_wantlist,
          is_watched: draft.is_watched,
          notes,
        }),
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Failed to update holding (${response.status})`);
      }
      notify({
        title: "Holding updated",
        description: "Your changes were saved.",
      });
      await upsertGraded(editing.card.id, draft);
      await loadHoldings();
    } catch (err: any) {
      notify({
        title: "Update failed",
        description: err.message || "Please try again.",
      });
    } finally {
      setSaving(false);
      setEditing(null);
    }
  };

  const deleteHolding = async () => {
    if (!token || !editing) return;
    if (!window.confirm(`Delete holding for ${editing.card.name}? This cannot be undone.`)) {
      return;
    }
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/holdings/${editing.holding_id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Failed to delete holding (${response.status})`);
      }
      notify({
        title: "Holding deleted",
        description: "The holding was removed.",
      });
      await loadHoldings();
    } catch (err: any) {
      notify({
        title: "Delete failed",
        description: err.message || "Please try again.",
      });
    } finally {
      setSaving(false);
      setEditing(null);
    }
  };

  const upsertGraded = async (cardId: number, draft: HoldingDraft) => {
    const grader = draft.meta.grader;
    const grade = draft.meta.grade;
    if (!grader || grader === "None" || !grade) {
      return;
    }
    try {
      await fetch(`${API_BASE}/graded/upsert`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ card_id: cardId, grader, grade }),
      });
    } catch {
      // ignore graded upsert failures
    }
  };

  const fetchGradedValue = async (cardId: number, request: GradedRequest) => {
    if (!token) return;
    const cooldownUntil = gradedCooldowns[cardId];
    if (cooldownUntil && cooldownUntil > Date.now()) {
      notify({
        title: "Please wait",
        description: "Try again in a minute to avoid API rate limits.",
      });
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/graded/fetch-price`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ card_id: cardId, grader: request.grader, grade: request.grade }),
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Failed to fetch graded value (${response.status})`);
      }
      const payload = (await response.json()) as { graded_id: number; market: number | null };
      setGradedMap((prev) => ({
        ...prev,
        [cardId]: {
          id: payload.graded_id,
          card_id: cardId,
          grader: request.grader,
          grade: request.grade,
        },
      }));
      setGradedPrices((prev) => ({ ...prev, [payload.graded_id]: { market: payload.market } }));
      notify({
        title: "Graded value updated",
        description: "Latest graded price stored.",
      });
      setGradedCooldowns((prev) => ({ ...prev, [cardId]: Date.now() + 60_000 }));
    } catch (err: any) {
      notify({
        title: "Graded lookup failed",
        description: err.message || "Please try again.",
      });
      setGradedCooldowns((prev) => ({ ...prev, [cardId]: Date.now() + 60_000 }));
    } finally {
    }
  };

  useEffect(() => {
    loadHoldings();
    loadSets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const filtered = holdings.filter((item) => {
    if (selectedSetId && item.set.id !== selectedSetId) {
      return false;
    }
    if (search.trim()) {
      const term = search.trim().toLowerCase();
      if (!item.card.name.toLowerCase().includes(term)) {
        return false;
      }
    }
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "set") {
      return a.set.name.localeCompare(b.set.name) || a.card.name.localeCompare(b.card.name);
    }
    if (sortBy === "alpha") {
      return a.card.name.localeCompare(b.card.name);
    }
    const aGraded = gradedMap[a.card.id];
    const bGraded = gradedMap[b.card.id];
    const aValue = aGraded ? gradedPrices[aGraded.id]?.market : priceMap[a.card.id]?.market;
    const bValue = bGraded ? gradedPrices[bGraded.id]?.market : priceMap[b.card.id]?.market;
    return (bValue ?? 0) - (aValue ?? 0);
  });

  useEffect(() => {
    if (!filtered.length) {
      setPriceMap({});
      return;
    }
    const handle = setTimeout(() => {
      fetchCardPrices(filtered.map((item) => item.card.id));
    }, 200);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtered.map((item) => item.card.id).join("|"), token]);

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Holdings</h2>
            <p className="text-sm text-white/50">Track quantities, conditions, and tags</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              className="rounded-full bg-base/60 px-4 py-2 text-sm text-white/70"
              onChange={(event) => {
                const value = event.target.value;
                setSelectedSetId(value ? Number(value) : null);
              }}
              value={selectedSetId ?? ""}
            >
              <option value="">All sets</option>
              {sets.map((set) => (
                <option key={set.id} value={set.id}>
                  {set.name}
                </option>
              ))}
            </select>
            <input
              className="w-56 rounded-full bg-base/60 px-4 py-2 text-sm text-white/70 placeholder:text-white/30"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search holdings"
              value={search}
            />
            <select
              className="rounded-full bg-base/60 px-4 py-2 text-sm text-white/70"
              onChange={(event) => setSortBy(event.target.value)}
              value={sortBy}
            >
              <option value="value">Sort: Value</option>
              <option value="set">Sort: Set</option>
              <option value="alpha">Sort: A–Z</option>
            </select>
            <div className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-xs text-white/60">
              <span>Size</span>
              <input
                className="accent-accent"
                max={260}
                min={150}
                onChange={(event) => setCardSize(Number(event.target.value))}
                type="range"
                value={cardSize}
              />
            </div>
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
                  title: "Add holdings from the catalog",
                  description: "Use the Add button on a card in the catalog.",
                })
              }
              type="button"
            >
              Add Holding
            </button>
          </div>
        </div>
        <div className="mt-3 text-xs text-white/50">
          Showing: {selectedSetId ? sets.find((set) => set.id === selectedSetId)?.name ?? "Set" : "All sets"}
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-2xl border border-white/10 bg-surface p-4 text-sm text-white/60">
          Loading holdings...
        </div>
      )}

      <div className="grid gap-4">
        {!loading && !sorted.length && (
          <div className="rounded-2xl border border-white/10 bg-surface p-5 text-sm text-white/60">
            No holdings yet. Add cards to your collection to see them here.
          </div>
        )}
        <div
          className="grid gap-4"
          style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${cardSize + 24}px, max-content))` }}
        >
          {sorted.map((item) => {
            const localImage = imageMap[item.card.id];
            const imageUrl = localImage
              ? `${window.location.origin}${localImage}`
              : `https://images.pokemontcg.io/${item.set.code}/${item.card.number}.png`;
            const graded = gradedMap[item.card.id];
            const gradedValue = graded ? gradedPrices[graded.id]?.market : null;
            return (
              <div
                key={item.holding_id}
                className="rounded-2xl border border-white/10 bg-surface p-4"
                style={{ width: `${cardSize + 24}px` }}
              >
                <button className="block" onClick={() => openCardDetail(item)} type="button">
                  <img
                    className="rounded-xl object-cover"
                    style={{ width: `${cardSize}px`, height: `${Math.round(cardSize * 1.33)}px` }}
                    src={imageUrl}
                    alt={item.card.name}
                  />
                </button>
                <div className="mt-4">
                  <h3 className="text-sm font-semibold">{item.card.name}</h3>
                  <p className="text-xs text-white/50">
                    {item.set.name} • {item.card.rarity ?? "Unknown rarity"}
                  </p>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="text-accent">
                      {priceMap[item.card.id]?.market
                        ? `$${priceMap[item.card.id].market?.toFixed(2)}`
                        : "—"}
                    </span>
                    <span className="text-white/40">NM</span>
                  </div>
                  {graded && (
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-white/70">
                        {graded.grader} {graded.grade}
                      </span>
                      <span className="text-accent">
                        {gradedValue ? `$${gradedValue.toFixed(2)}` : "—"}
                      </span>
                    </div>
                  )}
                  <p className="mt-2 text-xs text-white/60">
                    {item.condition} • Qty {item.quantity}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    {item.is_for_trade && (
                      <span className="rounded-full bg-accent/20 px-3 py-1 text-accent">Trade</span>
                    )}
                    {item.is_wantlist && (
                      <span className="rounded-full bg-white/10 px-3 py-1 text-white/70">Want</span>
                    )}
                  {item.is_watched && (
                    <span className="rounded-full bg-white/10 px-3 py-1 text-white/70">Watch</span>
                  )}
                  <button
                    className="rounded-full border border-white/10 px-3 py-1 text-white/60 hover:border-accent/60 hover:text-accent"
                    onClick={() => setGradingCard(item)}
                    type="button"
                  >
                    Get graded value
                  </button>
                  <button
                    className="rounded-full border border-white/10 px-3 py-1 text-white/60 hover:border-accent/60 hover:text-accent"
                    onClick={() => setEditing(item)}
                    type="button"
                  >
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      {editing && (
        <HoldingModal
          context={{ cardName: editing.card.name, setName: editing.set.name }}
          initial={{
            quantity: editing.quantity,
            condition: editing.condition,
            is_for_trade: editing.is_for_trade,
            is_wantlist: editing.is_wantlist,
            is_watched: editing.is_watched,
            notes: parseHoldingNotes(editing.notes).userNotes,
            meta: parseHoldingNotes(editing.notes).meta,
          }}
          onClose={() => setEditing(null)}
          onSave={saveHolding}
          onDelete={deleteHolding}
          open={!!editing}
        />
      )}
      {gradingCard && (
        <GradedValueModal
          cardName={gradingCard.card.name}
          initial={{
            grader: gradedMap[gradingCard.card.id]?.grader,
            grade: gradedMap[gradingCard.card.id]?.grade,
          }}
          onClose={() => setGradingCard(null)}
          onSubmit={(request) => {
            fetchGradedValue(gradingCard.card.id, request);
            setGradingCard(null);
          }}
          open={!!gradingCard}
        />
      )}
      <CardDetailModal
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        title={detailMeta?.name ?? "Card detail"}
        subtitle={
          detailMeta?.setName
            ? `${detailMeta.setName} • ${detailMeta?.number ?? ""} • ${detailMeta?.rarity ?? "Unknown rarity"}`
            : undefined
        }
        imageUrl={detailImage}
        latestPrice={
          detailMeta?.gradedId ? gradedPrices[detailMeta.gradedId]?.market ?? detailLatest : detailLatest
        }
        priceLabel={
          detailMeta?.grader && detailMeta?.grade
            ? `${detailMeta.grader} ${detailMeta.grade} market history`
            : "NM market history"
        }
        priceHistory={detailHistory}
        details={[
          { label: "Set", value: detailMeta?.setName },
          { label: "Number", value: detailMeta?.number },
          { label: "Rarity", value: detailMeta?.rarity },
          { label: "Condition", value: detailMeta?.condition },
          { label: "Quantity", value: detailMeta?.quantity },
          {
            label: "Grade",
            value:
              detailMeta?.grader && detailMeta?.grade
                ? `${detailMeta.grader} ${detailMeta.grade}`
                : undefined,
          },
          { label: "Supertype", value: detailMeta?.supertype },
          { label: "Subtypes", value: detailMeta?.subtypes?.join(", ") },
          { label: "Types", value: detailMeta?.types?.join(", ") },
          { label: "HP", value: detailMeta?.hp },
          { label: "Artist", value: detailMeta?.artist },
        ]}
      />
    </section>
  );
};

export default Holdings;
