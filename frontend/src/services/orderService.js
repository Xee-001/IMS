import api from "../api/axios";

export const getOrders = (skip = 0, limit = 100) =>
  api.get(`/orders/?skip=${skip}&limit=${limit}`).then((r) => r.data.data);

export const getOrder = (id) =>
  api.get(`/orders/${id}`).then((r) => r.data.data);

export const createOrder = (payload) =>
  api.post("/orders/", payload).then((r) => r.data.data);
