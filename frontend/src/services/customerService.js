import api from "../api/axios";

export const getCustomers = (skip = 0, limit = 100) =>
  api.get(`/customers/?skip=${skip}&limit=${limit}`).then((r) => r.data.data);

export const getCustomer = (id) =>
  api.get(`/customers/${id}`).then((r) => r.data.data);

export const createCustomer = (payload) =>
  api.post("/customers/", payload).then((r) => r.data.data);

export const updateCustomer = (id, payload) =>
  api.put(`/customers/${id}`, payload).then((r) => r.data.data);

export const deleteCustomer = (id) =>
  api.delete(`/customers/${id}`).then((r) => r.data);
