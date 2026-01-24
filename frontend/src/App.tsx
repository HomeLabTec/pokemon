import { Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Catalog from "./pages/Catalog";
import Holdings from "./pages/Holdings";
import Admin from "./pages/Admin";
import TopNav from "./components/TopNav";
import Sidebar from "./components/Sidebar";

const App = () => {
  return (
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
  );
};

export default App;
