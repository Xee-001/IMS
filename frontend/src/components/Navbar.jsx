import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/products", label: "Products" },
  { to: "/customers", label: "Customers" },
  { to: "/orders", label: "Orders" },
];

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">📦 IMS</div>
      <ul className="navbar-links">
        {links.map((l) => (
          <li key={l.to}>
            <NavLink
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {l.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
