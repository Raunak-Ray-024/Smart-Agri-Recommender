const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

// Turn FastAPI error responses into a readable message.
function readError(data, status) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(" ");
  }
  return `Request failed (status ${status}).`;
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Please check that the backend is running.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(readError(data, response.status));
  }
  return data;
}

export function getOptions() {
  return request("/api/options");
}

export function getRecommendations(payload) {
  return request("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getProduct(productId) {
  return request(`/api/products/${encodeURIComponent(productId)}`);
}