import { createContext, useContext, useEffect, useMemo, useState } from "react";

type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
};

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "pokvault_token";
const API_BASE =
  (import.meta as any).env?.VITE_API_URL ?? `${window.location.origin}/api`;

async function apiRequest(path: string, options: RequestInit = {}, token?: string | null) {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json();
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(!!token);
  const [error, setError] = useState<string | null>(null);

  const fetchMe = async (currentToken: string) => {
    const me = await apiRequest("/auth/me", { method: "GET" }, currentToken);
    setUser(me);
  };

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchMe(token)
      .catch((err) => {
        setError(err.message);
        setToken(null);
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const payload = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const accessToken = payload.access_token as string;
      setToken(accessToken);
      localStorage.setItem(TOKEN_KEY, accessToken);
      await fetchMe(accessToken);
    } catch (err: any) {
      setError(err.message || "Login failed");
      setToken(null);
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
  };

  const value = useMemo(
    () => ({ user, token, loading, error, login, logout }),
    [user, token, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
