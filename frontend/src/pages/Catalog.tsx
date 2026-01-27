import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import CardDetailModal from "../components/CardDetailModal";
import { useToast } from "../components/Toast";
import HoldingModal, { buildHoldingNotes, HoldingDraft } from "../components/HoldingModal";
import type { PricePoint } from "../components/PriceHistoryChart";

type SetRow = {
  id: number;
  code: string;
  name: string;
  series?: string | null;
};

type CardRow = {
  id: number;
  set_id: number;
  number: string;
  name: string;
  rarity?: string | null;
};

type CardImageRow = {
  kind: string;
  local_path?: string | null;
};

type CardDetail = {
  card: CardRow & {
    supertype?: string | null;
    subtypes?: string[] | null;
    types?: string[] | null;
    hp?: string | null;
    artist?: string | null;
  };
  images: CardImageRow[];
  price_history?: PricePoint[];
  latest_prices?: { market: number | null }[];
};

type PriceRow = {
  card_id: number;
  market: number | null;
  source: string;
  source_type: string;
};

const API_BASE =
  (import.meta as any).env?.VITE_API_URL ?? `${window.location.origin}/api`;

const Catalog = () => {
  const { notify } = useToast();
  const { token } = useAuth();
  const [sets, setSets] = useState<SetRow[]>([]);
  const [cards, setCards] = useState<CardRow[]>([]);
  const [selectedSetId, setSelectedSetId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [loadingSets, setLoadingSets] = useState(true);
  const [loadingCards, setLoadingCards] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageMap, setImageMap] = useState<Record<number, string>>({});
  const [addingMap, setAddingMap] = useState<Record<number, boolean>>({});
  const [activeCard, setActiveCard] = useState<CardRow | null>(null);
  const [activeSetName, setActiveSetName] = useState<string | undefined>(undefined);
  const [priceMap, setPriceMap] = useState<Record<number, PriceRow>>({});
  const [cardSize, setCardSize] = useState(220);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailCard, setDetailCard] = useState<CardDetail["card"] | null>(null);
  const [detailSet, setDetailSet] = useState<SetRow | null>(null);
  const [detailImage, setDetailImage] = useState("");
  const [detailHistory, setDetailHistory] = useState<PricePoint[]>([]);
  const [detailLatest, setDetailLatest] = useState<number | null>(null);

  const setById = useMemo(() => {
    const map = new Map<number, SetRow>();
    sets.forEach((set) => map.set(set.id, set));
    return map;
  }, [sets]);

  const fetchSets = async () => {
    if (!token) return;
    setLoadingSets(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/sets`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to load sets (${response.status})`);
      }
      const data = (await response.json()) as SetRow[];
      setSets(data);
      if (data.length && !selectedSetId) {
        setSelectedSetId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load sets");
    } finally {
      setLoadingSets(false);
    }
  };

  const fetchCards = async () => {
    if (!token) return;
    setLoadingCards(true);
    setError(null);
    try {
      let url = `${API_BASE}/cards/search`;
      const params = new URLSearchParams();
      if (selectedSetId) {
        params.set("set_id", String(selectedSetId));
      }
      if (search.trim()) {
        params.set("q", search.trim());
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to load cards (${response.status})`);
      }
      const data = (await response.json()) as CardRow[];
      setCards(data);
      const imageIds = data.slice(0, 24).map((card) => card.id);
      if (imageIds.length) {
        await fetchCardImages(imageIds);
      } else {
        setImageMap({});
      }
      if (data.length) {
        await fetchCardPrices(data.map((card) => card.id));
      } else {
        setPriceMap({});
      }
    } catch (err: any) {
      setError(err.message || "Failed to load cards");
    } finally {
      setLoadingCards(false);
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
          const detail = (await response.json()) as CardDetail;
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
    } catch (err) {
      setImageMap({});
    }
  };

  const fetchCardPrices = async (cardIds: number[]) => {
    if (!token) return;
    try {
      const next: Record<number, PriceRow> = {};
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
        const payload = (await response.json()) as { prices: PriceRow[] };
        payload.prices.forEach((price) => {
          next[price.card_id] = price;
        });
      }
      setPriceMap(next);
    } catch (err) {
      setPriceMap({});
    }
  };

  const addToHoldings = async (cardId: number, draft: HoldingDraft) => {
    if (!token) {
      notify({
        title: "Sign in required",
        description: "Please log in before adding holdings.",
      });
      return;
    }
    setAddingMap((prev) => ({ ...prev, [cardId]: true }));
    try {
      const notes = buildHoldingNotes(draft.meta, draft.notes);
      const response = await fetch(`${API_BASE}/holdings`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          card_id: cardId,
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
        throw new Error(message || `Failed to add holding (${response.status})`);
      }
      notify({
        title: "Added to holdings",
        description: "The card was added to your collection.",
      });
      await upsertGraded(cardId, draft);
    } catch (err: any) {
      notify({
        title: "Could not add holding",
        description: err.message || "Please try again.",
      });
    } finally {
      setAddingMap((prev) => ({ ...prev, [cardId]: false }));
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
      // ignore graded upsert failures on add
    }
  };

  useEffect(() => {
    fetchSets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (!selectedSetId && !search.trim()) return;
    const handle = setTimeout(() => {
      fetchCards();
    }, 250);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSetId, search, token]);

  const openCardDetail = async (card: CardRow) => {
    if (!token) return;
    setDetailOpen(true);
    setDetailSet(setById.get(card.set_id) ?? null);
    setDetailHistory([]);
    setDetailLatest(priceMap[card.id]?.market ?? null);
    try {
      const response = await fetch(`${API_BASE}/cards/${card.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("Failed to load card details");
      }
      const detail = (await response.json()) as CardDetail;
      const localLarge = detail.images.find((img) => img.kind === "large" && img.local_path)?.local_path;
      const localSmall = detail.images.find((img) => img.kind === "small" && img.local_path)?.local_path;
      const setRow = setById.get(card.set_id);
      const fallback = setRow?.code
        ? `https://images.pokemontcg.io/${setRow.code}/${card.number}.png`
        : "";
      setDetailImage(localLarge || localSmall ? `${window.location.origin}${localLarge || localSmall}` : fallback);
      setDetailCard(detail.card);
      setDetailHistory(detail.price_history ?? []);
      setDetailLatest(detail.latest_prices?.[0]?.market ?? priceMap[card.id]?.market ?? null);
    } catch {
      setDetailCard(card as CardDetail["card"]);
    }
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-surface p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Card Catalog</h2>
            <p className="text-sm text-white/50">Search sets, types, rarities, and variants</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              className="rounded-full bg-base/60 px-4 py-2 text-sm text-white/70"
              disabled={loadingSets || !sets.length}
              onChange={(event) => {
                const value = event.target.value;
                setSelectedSetId(value ? Number(value) : null);
              }}
              value={selectedSetId ?? ""}
            >
              {loadingSets && <option value="">Loading sets...</option>}
              {!loadingSets && <option value="">All sets</option>}
              {!loadingSets && !sets.length && <option value="">No sets found</option>}
              {sets.map((set) => (
                <option key={set.id} value={set.id}>
                  {set.name}
                </option>
              ))}
            </select>
            <input
              className="w-56 rounded-full bg-base/60 px-4 py-2 text-sm text-white/70 placeholder:text-white/30"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search cards"
              value={search}
            />
            <div className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-xs text-white/60">
              <span>Size</span>
              <input
                className="accent-accent"
                max={280}
                min={160}
                onChange={(event) => setCardSize(Number(event.target.value))}
                type="range"
                value={cardSize}
              />
            </div>
            <button
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 hover:border-accent/60 hover:text-accent"
              onClick={fetchCards}
              type="button"
            >
              Filters
            </button>
            <button
              className="rounded-full border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10"
              onClick={() =>
                notify({
                  title: "Saved views require an account",
                  description: "Create a user in the admin panel to save views.",
                })
              }
              type="button"
            >
              Save View
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loadingCards && (
        <div className="rounded-2xl border border-white/10 bg-surface p-4 text-sm text-white/60">
          Loading cards...
        </div>
      )}

      {!loadingCards && (
        <div
          className="grid gap-4"
          style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${cardSize + 24}px, max-content))` }}
        >
          {cards.map((card) => {
            const setRow = setById.get(card.set_id);
            const setCode = setRow?.code ?? "";
            const localImage = imageMap[card.id];
            const imageUrl = localImage
              ? `${window.location.origin}${localImage}`
              : setCode
                ? `https://images.pokemontcg.io/${setCode}/${card.number}.png`
                : "";
            return (
              <div
                key={card.id}
                className="rounded-2xl border border-white/10 bg-surface p-4"
                style={{ width: `${cardSize + 24}px` }}
              >
                {imageUrl ? (
                  <button
                    className="block"
                    onClick={() => openCardDetail(card)}
                    type="button"
                  >
                    <img
                      className="rounded-xl object-cover"
                      style={{ width: `${cardSize}px`, height: `${Math.round(cardSize * 1.33)}px` }}
                      src={imageUrl}
                      alt={card.name}
                    />
                  </button>
                ) : (
                  <div
                    className="rounded-xl bg-base/50"
                    style={{ width: `${cardSize}px`, height: `${Math.round(cardSize * 1.33)}px` }}
                  />
                )}
                <div className="mt-4">
                  <h3 className="text-sm font-semibold">{card.name}</h3>
                  <p className="text-xs text-white/50">
                    {setRow?.name ?? "Unknown set"} • {card.rarity ?? "Unknown rarity"}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-accent">
                      {priceMap[card.id]?.market ? `$${priceMap[card.id].market.toFixed(2)}` : "—"}
                    </span>
                    <span className="text-white/40">NM</span>
                  </div>
                  <button
                    className="mt-3 w-full rounded-full border border-accent/40 px-3 py-2 text-xs text-accent hover:bg-accent/10 disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!!addingMap[card.id]}
                    onClick={() => {
                      const setRow = setById.get(card.set_id);
                      setActiveSetName(setRow?.name);
                      setActiveCard(card);
                    }}
                    type="button"
                  >
                    {addingMap[card.id] ? "Adding..." : "Add to holdings"}
                  </button>
                </div>
              </div>
            );
          })}
          {!cards.length && !loadingCards && (
            <div className="rounded-2xl border border-white/10 bg-surface p-4 text-sm text-white/60">
              No cards found. Try another set or search.
            </div>
          )}
        </div>
      )}

      {activeCard && (
        <HoldingModal
          context={{
            cardName: activeCard.name,
            setName: activeSetName,
          }}
          onClose={() => setActiveCard(null)}
          onSave={(draft) => {
            addToHoldings(activeCard.id, draft);
            setActiveCard(null);
          }}
          open={!!activeCard}
        />
      )}
      <CardDetailModal
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        title={detailCard?.name ?? "Card detail"}
        subtitle={
          detailSet
            ? `${detailSet.name} • ${detailCard?.number ?? ""} • ${detailCard?.rarity ?? "Unknown rarity"}`
            : undefined
        }
        imageUrl={detailImage}
        latestPrice={detailLatest}
        priceLabel="NM market history"
        priceHistory={detailHistory}
        details={[
          { label: "Set", value: detailSet?.name },
          { label: "Series", value: detailSet?.series },
          { label: "Number", value: detailCard?.number },
          { label: "Rarity", value: detailCard?.rarity },
          { label: "Supertype", value: detailCard?.supertype },
          { label: "Subtypes", value: detailCard?.subtypes?.join(", ") },
          { label: "Types", value: detailCard?.types?.join(", ") },
          { label: "HP", value: detailCard?.hp },
          { label: "Artist", value: detailCard?.artist },
        ]}
      />
    </section>
  );
};

export default Catalog;
