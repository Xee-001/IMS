import { useEffect, useState } from "react";
import { getOrders, createOrder } from "../services/orderService";
import { getProducts } from "../services/productService";
import { getCustomers } from "../services/customerService";
import Modal from "../components/Modal";
import Alert from "../components/Alert";
import Spinner from "../components/Spinner";

const EMPTY_FORM = { customer_id: "", product_id: "", quantity: "" };

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Live preview of total price
  const selectedProduct = products.find((p) => p.id === form.product_id);
  const previewTotal =
    selectedProduct && form.quantity > 0
      ? (selectedProduct.price * Number(form.quantity)).toFixed(2)
      : null;

  const load = () =>
    Promise.all([getOrders(), getProducts(), getCustomers()])
      .then(([o, p, c]) => {
        setOrders(o);
        setProducts(p);
        setCustomers(c);
      })
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setError("");
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await createOrder({ ...form, quantity: parseInt(form.quantity, 10) });
      setSuccess("Order placed successfully. Stock has been updated.");
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.response?.data?.message || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  // Resolve IDs to names for display
  const customerMap = Object.fromEntries(customers.map((c) => [c.id, c.name]));
  const productMap = Object.fromEntries(products.map((p) => [p.id, p.name]));

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Orders</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + Place Order
        </button>
      </div>

      <Alert type="success" message={success} onClose={() => setSuccess("")} />
      <Alert type="error" message={error} onClose={() => setError("")} />

      {orders.length === 0 ? (
        <p className="empty-text">No orders yet. Click "Place Order" to create one.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Product</th>
                <th>Qty</th>
                <th>Total</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td className="mono">{o.id.slice(0, 8)}…</td>
                  <td>{customerMap[o.customer_id] || o.customer_id.slice(0, 8)}</td>
                  <td>{productMap[o.product_id] || o.product_id.slice(0, 8)}</td>
                  <td>{o.quantity}</td>
                  <td>${o.total_price.toFixed(2)}</td>
                  <td>{new Date(o.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <Modal title="Place New Order" onClose={() => setShowModal(false)}>
          <Alert type="error" message={error} onClose={() => setError("")} />
          <form onSubmit={handleSubmit} className="form">
            <label className="form-label">
              Customer *
              <select
                className="form-input"
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                required
              >
                <option value="">— select customer —</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.customer_code})
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label">
              Product *
              <select
                className="form-input"
                value={form.product_id}
                onChange={(e) => setForm({ ...form, product_id: e.target.value })}
                required
              >
                <option value="">— select product —</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.stock === 0}>
                    {p.name} — ${p.price.toFixed(2)} (stock: {p.stock})
                    {p.stock === 0 ? " [OUT OF STOCK]" : ""}
                  </option>
                ))}
              </select>
            </label>

            {selectedProduct && (
              <div className="stock-hint">
                Available stock: <strong>{selectedProduct.stock}</strong> units
              </div>
            )}

            <label className="form-label">
              Quantity *
              <input
                className="form-input"
                type="number"
                min="1"
                max={selectedProduct?.stock || undefined}
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                required
              />
            </label>

            {previewTotal && (
              <div className="price-preview">
                Estimated Total: <strong>${previewTotal}</strong>
              </div>
            )}

            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Placing…" : "Place Order"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
