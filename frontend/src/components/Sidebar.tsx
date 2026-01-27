import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/catalog", label: "Catalog" },
  { to: "/holdings", label: "Holdings" },
  { to: "/account", label: "Account" },
  { to: "/admin", label: "Admin" },
];

const Sidebar = () => {
  return (
    <aside className="hidden w-64 border-r border-white/10 bg-surface/40 p-6 lg:block">
      <div className="space-y-4">
        <div className="text-xs uppercase text-white/40">Collections</div>
        <nav className="space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `block rounded-xl px-4 py-3 text-sm transition ${
                  isActive ? "bg-accent/20 text-accent" : "text-white/70 hover:bg-white/5"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
