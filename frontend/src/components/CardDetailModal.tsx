import PriceHistoryChart, { PricePoint } from "./PriceHistoryChart";

type DetailItem = {
  label: string;
  value?: string | number | null;
};

type CardDetailModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  imageUrl: string;
  details: DetailItem[];
  priceHistory: PricePoint[];
  priceLabel: string;
  latestPrice?: number | null;
};

const CardDetailModal = ({
  open,
  onClose,
  title,
  subtitle,
  imageUrl,
  details,
  priceHistory,
  priceLabel,
  latestPrice,
}: CardDetailModalProps) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="relative w-full max-w-6xl overflow-hidden rounded-3xl border border-white/10 bg-surface shadow-xl">
        <button
          className="absolute right-4 top-4 rounded-full border border-white/10 bg-base/70 px-3 py-1 text-xs text-white/60 hover:border-accent/60 hover:text-accent"
          onClick={onClose}
          type="button"
        >
          Close
        </button>
        <div className="grid gap-6 p-6 lg:grid-cols-[minmax(280px,420px)_1fr]">
          <div className="flex items-center justify-center">
            <img className="max-h-[80vh] w-full rounded-2xl object-contain" src={imageUrl} alt={title} />
          </div>
          <div className="space-y-5">
            <div>
              <h3 className="text-2xl font-semibold">{title}</h3>
              {subtitle && <p className="text-sm text-white/50">{subtitle}</p>}
              <div className="mt-2 text-lg text-accent">
                {latestPrice ? `$${latestPrice.toFixed(2)}` : "—"}
              </div>
            </div>
            <div className="grid gap-2 rounded-2xl border border-white/10 bg-base/50 p-4 text-sm">
              {details
                .filter((item) => item.value !== undefined && item.value !== null && item.value !== "")
                .map((item) => (
                  <div key={item.label} className="flex items-center justify-between gap-4">
                    <span className="text-white/50">{item.label}</span>
                    <span className="text-white/80">{item.value}</span>
                  </div>
                ))}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-white/60">
                <span>{priceLabel}</span>
              </div>
              <PriceHistoryChart data={priceHistory} label={priceLabel} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CardDetailModal;
