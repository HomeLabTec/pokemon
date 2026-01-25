import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type ToastMessage = {
  id: string;
  title: string;
  description?: string;
};

type ToastContextValue = {
  notify: (message: Omit<ToastMessage, "id">) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const TOAST_DURATION = 3500;

const createToastId = () => {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `toast-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
};

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const notify = useCallback((message: Omit<ToastMessage, "id">) => {
    const toast: ToastMessage = {
      id: createToastId(),
      ...message,
    };
    setToasts((prev) => [...prev, toast]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== toast.id));
    }, TOAST_DURATION);
  }, []);

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-6 top-24 z-50 flex w-80 flex-col gap-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto rounded-2xl border border-white/10 bg-surface/95 p-4 shadow-lg backdrop-blur"
          >
            <p className="text-sm font-semibold text-white">{toast.title}</p>
            {toast.description && (
              <p className="mt-1 text-xs text-white/60">{toast.description}</p>
            )}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};
