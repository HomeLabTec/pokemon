import { useEffect, useState } from "react";

export type GradedRequest = {
  grader: string;
  grade: string;
};

const GradedValueModal = ({
  open,
  onClose,
  onSubmit,
  initial,
  cardName,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (draft: GradedRequest) => void;
  initial?: Partial<GradedRequest>;
  cardName: string;
}) => {
  const [grader, setGrader] = useState("PSA");
  const [grade, setGrade] = useState("");

  useEffect(() => {
    if (!open) return;
    setGrader(initial?.grader ?? "PSA");
    setGrade(initial?.grade ?? "");
  }, [open, initial]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-surface p-6 text-white shadow-2xl">
        <div className="mb-4">
          <h3 className="text-xl font-semibold">Get graded value</h3>
          <p className="text-sm text-white/50">{cardName}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm text-white/70">
            Grader
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              onChange={(event) => setGrader(event.target.value)}
              value={grader}
            >
              <option value="PSA">PSA</option>
              <option value="BGS">BGS</option>
              <option value="CGC">CGC</option>
              <option value="SGC">SGC</option>
              <option value="TAG">TAG</option>
            </select>
          </label>
          <label className="text-sm text-white/70">
            Grade
            <input
              className="mt-2 w-full rounded-xl border border-white/10 bg-base/60 px-3 py-2 text-sm text-white"
              onChange={(event) => setGrade(event.target.value)}
              placeholder="10, 9.5, 9, etc."
              type="text"
              value={grade}
            />
          </label>
        </div>
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
            onClick={() => onSubmit({ grader, grade })}
            type="button"
          >
            Fetch value
          </button>
        </div>
      </div>
    </div>
  );
};

export default GradedValueModal;
