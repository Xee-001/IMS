import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProducts } from "../services/productService";
import { getCustomers } from "../services/customerService";
import { getOrders } from "../services/orderService";
import Spinner from "../components/Spinner";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getProducts(), getCustomers(), getOrders()])
      .then(([products, customers, orders]) => {
        const lowStock = products.filter((p) => p.stock <= 5);
        const totalRevenue = orders.reduce((s, o) => s + o.total_price, 0);
        setStats({ products, customers, orders, lowStock, totalRevenue });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  const cards = [
    { label: "Total Products", value: stats.products.length, to: "/products", color: "card-blue" },
    { label: "Total Customers", value: stats.customers.length, to: "/customers", color: "card-green" },
    { label: "Total Orders", value: stats.orders.length, to: "/orders", color: "card-purple" },
    {
      label: "Total Revenue",
      value: `$${stats.totalRevenue.toFixed(2)}`,
      to: "/orders",
      color: "card-orange",
    },
  ];

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <div className="stats-grid">
        {cards.map((c) => (
          <Link key={c.label} to={c.to} className={`stat-card ${c.color}`}>
            <div className="stat-value">{c.value}</div>
            <div className="stat-label">{c.label}</div>
          </Link>
        ))}
      </div>

      {stats.lowStock.length > 0 && (
        <div className="low-stock-panel">
          <h2 className="section-title">⚠️ Low Stock Alert (≤ 5 units)</h2>
          <table className="table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              {stats.lowStock.map((p) => (
                <tr key={p.id} className="row-warn">
                  <td>{p.sku}</td>
                  <td>{p.name}</td>
                  <td>{p.stock}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="recent-orders-panel">
        <h2 className="section-title">Recent Orders</h2>
        {stats.orders.length === 0 ? (
          <p className="empty-text">No orders yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Qty</th>
                <th>Total</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {stats.orders.slice(0, 5).map((o) => (
                <tr key={o.id}>
                  <td className="mono">{o.id.slice(0, 8)}…</td>
                  <td>{o.quantity}</td>
                  <td>${o.total_price.toFixed(2)}</td>
                  <td>{new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
