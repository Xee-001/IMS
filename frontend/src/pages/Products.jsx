import { useEffect, useState } from "react";
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from "../services/productService";
import Modal from "../components/Modal";
import Alert from "../components/Alert";
import Spinner from "../components/Spinner";

const EMPTY_FORM = { sku: "", name: "", description: "", price: "", stock: "" };

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null); // null = create, object = edit
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () =>
    getProducts()
      .then(setProducts)
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setError("");
    setShowModal(true);
  };

  const openEdit = (p) => {
    setEditTarget(p);
    setForm({
      sku: p.sku,
      name: p.name,
      description: p.description || "",
      price: p.price,
      stock: p.stock,
    });
    setError("");
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const payload = {
      ...form,
      price: parseFloat(form.price),
      stock: parseInt(form.stock, 10),
    };
    try {
      if (editTarget) {
        const { sku, ...updatePayload } = payload; // SKU is immutable
        await updateProduct(editTarget.id, updatePayload);
        setSuccess("Product updated successfully.");
      } else {
        await createProduct(payload);
        setSuccess("Product created successfully.");
      }
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.response?.data?.message || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this product?")) return;
    try {
      await deleteProduct(id);
      setSuccess("Product deleted.");
      load();
    } catch (err) {
      setError(err.response?.data?.message || "Could not delete product.");
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Products</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + Add Product
        </button>
      </div>

      <Alert type="success" message={success} onClose={() => setSuccess("")} />
      <Alert type="error" message={error} onClose={() => setError("")} />

      {products.length === 0 ? (
        <p className="empty-text">No products yet. Click "Add Product" to create one.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className={p.stock === 0 ? "row-danger" : p.stock <= 5 ? "row-warn" : ""}>
                  <td className="mono">{p.sku}</td>
                  <td>{p.name}</td>
                  <td>${p.price.toFixed(2)}</td>
                  <td>
                    <span className={`badge ${p.stock === 0 ? "badge-red" : p.stock <= 5 ? "badge-yellow" : "badge-green"}`}>
                      {p.stock}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-secondary" onClick={() => openEdit(p)}>
                      Edit
                    </button>{" "}
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(p.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <Modal
          title={editTarget ? "Edit Product" : "Add Product"}
          onClose={() => setShowModal(false)}
        >
          <Alert type="error" message={error} onClose={() => setError("")} />
          <form onSubmit={handleSubmit} className="form">
            <label className="form-label">
              SKU *
              <input
                className="form-input"
                value={form.sku}
                onChange={(e) => setForm({ ...form, sku: e.target.value })}
                required
                disabled={!!editTarget}
                placeholder="e.g. WIDGET-001"
              />
            </label>
            <label className="form-label">
              Name *
              <input
                className="form-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="e.g. Blue Widget"
              />
            </label>
            <label className="form-label">
              Description
              <textarea
                className="form-input"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
                placeholder="Optional"
              />
            </label>
            <div className="form-row">
              <label className="form-label">
                Price ($) *
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  required
                />
              </label>
              <label className="form-label">
                Stock *
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  value={form.stock}
                  onChange={(e) => setForm({ ...form, stock: e.target.value })}
                  required
                />
              </label>
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Saving…" : editTarget ? "Update" : "Create"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
