import axios from "axios";

// The Gemini API key NEVER lives in the frontend. The browser only talks to our
// own backend, which holds the key in environment variables.
const baseURL = import.meta.env.VITE_API_BASE_URL || "";

const client = axios.create({ baseURL, timeout: 90000 });

function detailFrom(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
  return error?.message || "Unexpected error";
}

async function request(promise) {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw new Error(detailFrom(error));
  }
}

export const api = {
  health: () => request(client.get("/api/health")),

  dashboardStats: () => request(client.get("/api/dashboard/stats")),

  listPolicies: () => request(client.get("/api/policies")),
  getPolicy: (id) => request(client.get(`/api/policies/${id}`)),
  addTextPolicy: (payload) => request(client.post("/api/policies/text", payload)),
  deletePolicy: (id) => request(client.delete(`/api/policies/${id}`)),
  uploadPolicy: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request(
      client.post("/api/policies/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
    );
  },

  getPrompts: () => request(client.get("/api/prompts")),

  analyze: (payload) => request(client.post("/api/complaints/analyze", payload)),
  compare: (payload) => request(client.post("/api/complaints/compare", payload)),
  history: () => request(client.get("/api/complaints")),
  getRecord: (id) => request(client.get(`/api/complaints/${id}`)),
  reviewRecord: (id, payload) =>
    request(client.patch(`/api/complaints/${id}/review`, payload)),
};

export default api;
