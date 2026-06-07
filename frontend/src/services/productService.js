import api from "../api/axios";

export const getProducts = (skip = 0, limit = 100) =>
  api.get(`/products/?skip=${skip}&limit=${limit}`).then((r) => r.data.data);

export const getProduct = (id) =>
  api.get(`/products/${id}`).then((r) => r.data.data);

export const createProduct = (payload) =>
  api.post("/products/", payload).then((r) => r.data.data);

export const updateProduct = (id, payload) =>
  api.put(`/products/${id}`, payload).then((r) => r.data.data);

export const deleteProduct = (id) =>
  api.delete(`/products/${id}`).then((r) => r.data);
