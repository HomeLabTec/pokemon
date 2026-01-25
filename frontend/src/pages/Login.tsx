import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const Login = () => {
  const navigate = useNavigate();
  const { login, error, loading, token } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      navigate("/");
    }
  }, [token, navigate]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);
    try {
      await login(email.trim(), password);
      navigate("/");
    } catch (err: any) {
      setLocalError(err.message || "Login failed");
    }
  };

  return (
    <div className="min-h-screen bg-base text-white">
      <div className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <div className="w-full rounded-3xl border border-white/10 bg-surface/70 p-8 shadow-xl">
          <div className="mb-6">
            <h1 className="text-3xl font-semibold text-accent">PokeVault</h1>
            <p className="text-sm text-white/60">Sign in to your collection</p>
          </div>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm text-white/70">
              Email
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none ring-1 ring-transparent focus:ring-accent/60"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={email}
              />
            </label>
            <label className="block text-sm text-white/70">
              Password
              <input
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none ring-1 ring-transparent focus:ring-accent/60"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </label>
            {(localError || error) && (
              <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
                {localError || error}
              </div>
            )}
            <button
              className="w-full rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-black hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={loading}
              type="submit"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
