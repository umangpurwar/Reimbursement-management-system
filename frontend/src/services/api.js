import axios from "axios";
import router from "../router";

// =======================
// ⚙️ CONFIG
// =======================
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// =======================
// 🔐 TOKEN HELPERS
// =======================
const getAccessToken = () => localStorage.getItem("access_token");
const getRefreshToken = () => localStorage.getItem("refresh_token");

const setTokens = (access, refresh) => {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
};

const clearAll = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
};

// =======================
// 🔁 REFRESH STATE
// =======================
let isRefreshing = false;
let subscribers = [];

const subscribeTokenRefresh = (cb) => {
  subscribers.push(cb);
};

const onRefreshed = (token) => {
  subscribers.forEach((cb) => cb(token));
  subscribers = [];
};

// =======================
// 🔐 REQUEST INTERCEPTOR
// =======================
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// =======================
// 🔄 RESPONSE INTERCEPTOR
// =======================
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (!error.response || error.response.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      logout();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      logout();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        subscribeTokenRefresh((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(api(originalRequest));
        });
      });
    }

    isRefreshing = true;

    try {
      const res = await axios.post(`${BASE_URL}token/refresh/`, {
        refresh: refreshToken,
      });

      const newAccess = res.data.access;

      setTokens(newAccess, null);
      onRefreshed(newAccess);

      originalRequest.headers.Authorization = `Bearer ${newAccess}`;
      return api(originalRequest);
    } catch (err) {
      logout();
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

// =======================
// 🔐 AUTH FUNCTIONS
// =======================
export const login = async (credentials) => {
  // 1. Get tokens
  const res = await api.post("token/", credentials);

  setTokens(res.data.access, res.data.refresh);

  // 2. Get user details (IMPORTANT)
  const userRes = await api.get("users/me/");

  localStorage.setItem("role", userRes.data.role);
  localStorage.setItem("username", userRes.data.username);

  return res.data;
};

export const logout = () => {
  clearAll();
  router.push("/login");
};

// =======================
// 📦 API FUNCTIONS
// =======================

// 💸 Expenses
export const createExpense = (data) =>
  api.post("expenses/", data);

export const getMyExpenses = () =>
  api.get("expenses/my/");

// 👨‍💼 Approvals
export const getPendingApprovals = () =>
  api.get("approvals/pending/");

export const takeApprovalAction = (id, action) =>
  api.patch(`approvals/${id}/action/`, { action });

// 🧾 OCR
export const scanReceipt = (file) => {
  const formData = new FormData();
  formData.append("image", file);

  return api.post("receipts/scan/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const retryScan = (id) =>
  api.post(`receipts/${id}/retry/`);

// 🌍 Currency
export const getCurrencies = () =>
  api.get("receipts/currencies/");

export const convertCurrency = (data) =>
  api.post("receipts/convert/", data);

export default api;