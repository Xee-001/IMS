import { useEffect, useState } from "react";
import {
  getCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
} from "../services/customerService";
import Modal from "../components/Modal";
import Alert from "../components/Alert";
import Spinner from "../components/Spinner";

const EMPTY_FORM = { customer_code: "", name: "", email: "", phone: "" };

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = () =>
    getCustomers()
      .then(setCustomers)
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setError("");
    setShowModal(true);
  };

  const openEdit = (c) => {
    setEditTarget(c);
    setForm({ customer_code: c.customer_code, name: c.name, email: c.email, phone: c.phone });
    setError("");
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (editTarget) {
        const { customer_code, ...updatePayload } = form; // code is immutable
        await updateCustomer(editTarget.id, updatePayload);
        setSuccess("Customer updated.");
      } else {
        await createCustomer(form);
        setSuccess("Customer created.");
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
    if (!window.confirm("Delete this customer?")) return;
    try {
      await deleteCustomer(id);
      setSuccess("Customer deleted.");
      load();
    } catch (err) {
      setError(err.response?.data?.message || "Could not delete customer.");
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Customers</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + Add Customer
        </button>
      </div>

      <Alert type="success" message={success} onClose={() => setSuccess("")} />
      <Alert type="error" message={error} onClose={() => setError("")} />

      {customers.length === 0 ? (
        <p className="empty-text">No customers yet. Click "Add Customer" to create one.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id}>
                  <td className="mono">{c.customer_code}</td>
                  <td>{c.name}</td>
                  <td>{c.email}</td>
                  <td>{c.phone}</td>
                  <td>
                    <button className="btn btn-sm btn-secondary" onClick={() => openEdit(c)}>
                      Edit
                    </button>{" "}
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(c.id)}>
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
          title={editTarget ? "Edit Customer" : "Add Customer"}
          onClose={() => setShowModal(false)}
        >
          <Alert type="error" message={error} onClose={() => setError("")} />
          <form onSubmit={handleSubmit} className="form">
            <label className="form-label">
              Customer Code *
              <input
                className="form-input"
                value={form.customer_code}
                onChange={(e) => setForm({ ...form, customer_code: e.target.value })}
                required
                disabled={!!editTarget}
                placeholder="e.g. CUST-001"
              />
            </label>
            <label className="form-label">
              Name *
              <input
                className="form-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="e.g. Alice Smith"
              />
            </label>
            <label className="form-label">
              Email *
              <input
                className="form-input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
                placeholder="alice@example.com"
              />
            </label>
            <label className="form-label">
              Phone *
              <input
                className="form-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                required
                placeholder="+1-555-0100"
              />
            </label>
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
