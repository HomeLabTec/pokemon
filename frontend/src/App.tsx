import { Route, Routes, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Catalog from "./pages/Catalog";
import Holdings from "./pages/Holdings";
import Admin from "./pages/Admin";
import Login from "./pages/Login";
import TopNav from "./components/TopNav";
import Sidebar from "./components/Sidebar";
import RequireAuth from "./auth/RequireAuth";

const App = () => {
  const location = useLocation();
  const isLogin = location.pathname === "/login";

  if (isLogin) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    );
  }

  return (
    <RequireAuth>
      <div className="min-h-screen bg-base text-white">
        <TopNav />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-6 space-y-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/catalog" element={<Catalog />} />
              <Route path="/holdings" element={<Holdings />} />
              <Route path="/admin" element={<Admin />} />
            </Routes>
          </main>
        </div>
      </div>
    </RequireAuth>
  );
};

export default App;
