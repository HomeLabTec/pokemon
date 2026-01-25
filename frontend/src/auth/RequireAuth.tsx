import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

const RequireAuth = ({ children }: { children: JSX.Element }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-base text-white">
        <div className="rounded-2xl border border-white/10 bg-surface/60 px-6 py-4 text-sm">
          Loading account...
        </div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default RequireAuth;
