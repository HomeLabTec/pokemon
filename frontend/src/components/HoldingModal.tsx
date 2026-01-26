import { useEffect, useState } from "react";

type HoldingMeta = {
  grade?: string;
  finish?: string;
};

export type HoldingDraft = {
  quantity: number;
  condition: string;
  is_for_trade: boolean;
  is_wantlist: boolean;
  is_watched: boolean;
  notes: string;
  meta: HoldingMeta;
};

export type HoldingModalContext = {
  cardName: string;
  setName?: string;
};

const META_PREFIX = "__pv_meta__:";

export const parseHoldingNotes = (notes?: string | null) => {
  if (!notes) {
    return { meta: {}, userNotes: "" };
  }
  if (notes.startsWith(META_PREFIX)) {
    const [firstLine, ...rest] = notes.split("\n");
    try {
      const raw = firstLine.slice(META_PREFIX.length).trim();
      const meta = raw ? (JSON.parse(raw) as HoldingMeta) : {};
      return { meta, userNotes: rest.join("\n") };
    } catch {
      return { meta: {}, userNotes: notes };
    }
  }
  return { meta: {}, userNotes: notes };
};

export const buildHoldingNotes = (meta: HoldingMeta, userNotes: string) => {
  const cleanedNotes = userNotes.trim();
  const metaEntries = Object.entries(meta).filter(([, value]) => value);
  if (!metaEntries.length) {
    return cleanedNotes;
  }
  const payload = JSON.stringify(
    Object.fromEntries(metaEntries.map(([key, value]) => [key, value]))
  );
  return cleanedNotes ? `${META_PREFIX}${payload}\n${cleanedNotes}` : `${META_PREFIX}${payload}`;
};

const HoldingModal = ({
  open,
  onClose,
  onSave,
  context,
  initial,
}: {
  open: boolean;
  onClose: () => void;
  onSave: (draft: HoldingDraft) => void;
  context: HoldingModalContext;
  initial?: Partial<HoldingDraft>;
}) => {
  const [quantity, setQuantity] = useState(1);
  const [condition, setCondition] = useState("NM");
  const [grade, setGrade] = useState("");
  const [finish, setFinish] = useState("normal");
  const [isForTrade, setIsForTrade] = useState(false);
  const [isWantlist, setIsWantlist] = useState(false);
  const [isWatched, setIsWatched] = useState(false);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!open) return;
    const meta = initial?.meta ?? {};
    setQuantity(initial?.quantity ?? 1);
    setCondition(initial?.condition ?? "NM");
    setGrade(meta.grade ?? "");
    setFinish(meta.finish ?? "normal");
    setIsForTrade(initial?.is_for_trade ?? false);
    setIsWantlist(initial?.is_wantlist ?? false);
    setIsWatched(initial?.is_watched ?? false);
    setNotes(initial?.notes ?? "");
  }, [open, initial]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-surface p-6 text-white shadow-2xl">
        <div className="mb-4">
          <h3 className="text-xl font-semibold">{context.cardName}</h3>
          {context.setName && <p className="text-sm text-white/50">{context.setName}</p>}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm text-white/70">
            Quantity
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              min={1}
              onChange={(event) => setQuantity(Number(event.target.value))}
              type="number"
              value={quantity}
            />
          </label>
          <label className="text-sm text-white/70">
            Condition
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              onChange={(event) => setCondition(event.target.value)}
              value={condition}
            >
              <option value="NM">NM</option>
              <option value="LP">LP</option>
              <option value="MP">MP</option>
              <option value="HP">HP</option>
              <option value="DMG">DMG</option>
            </select>
          </label>
          <label className="text-sm text-white/70">
            Grade (optional)
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              onChange={(event) => setGrade(event.target.value)}
              placeholder="PSA 10, BGS 9.5, etc."
              type="text"
              value={grade}
            />
          </label>
          <label className="text-sm text-white/70">
            Finish
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              onChange={(event) => setFinish(event.target.value)}
              value={finish}
            >
              <option value="normal">Normal</option>
              <option value="holo">Holofoil</option>
              <option value="reverse_holo">Reverse Holofoil</option>
              <option value="other">Other</option>
            </select>
          </label>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3 text-xs text-white/70">
          <label className="flex items-center gap-2">
            <input
              checked={isForTrade}
              onChange={(event) => setIsForTrade(event.target.checked)}
              type="checkbox"
            />
            For trade
          </label>
          <label className="flex items-center gap-2">
            <input
              checked={isWantlist}
              onChange={(event) => setIsWantlist(event.target.checked)}
              type="checkbox"
            />
            Wantlist
          </label>
          <label className="flex items-center gap-2">
            <input
              checked={isWatched}
              onChange={(event) => setIsWatched(event.target.checked)}
              type="checkbox"
            />
            Watch
          </label>
        </div>
        <label className="mt-4 block text-sm text-white/70">
          Notes
          <textarea
            className="mt-2 min-h-[96px] w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
            onChange={(event) => setNotes(event.target.value)}
            value={notes}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/70 hover:bg-white/10"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-black hover:bg-accent/90"
            onClick={() =>
              onSave({
                quantity,
                condition,
                is_for_trade: isForTrade,
                is_wantlist: isWantlist,
                is_watched: isWatched,
                notes,
                meta: { grade, finish },
              })
            }
            type="button"
          >
            Save holding
          </button>
        </div>
      </div>
    </div>
  );
};

export default HoldingModal;
