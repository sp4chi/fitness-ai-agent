const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function signup(email: string, password: string, fullName: string) {
  const data = await request("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  // FastAPI's OAuth2PasswordRequestForm expects form-encoded data
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || "Login failed");
  }
  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

export const getProfile = () => request("/profile");
export const updateProfile = (payload: Record<string, unknown>) =>
  request("/profile", { method: "PUT", body: JSON.stringify(payload) });

export const generatePlan = (notes: string) =>
  request("/plan/generate", { method: "POST", body: JSON.stringify({ notes }) });

export const getPlanHistory = () => request("/plan/history");

export const logWorkout = (payload: Record<string, unknown>) =>
  request("/logs/workout", { method: "POST", body: JSON.stringify(payload) });

export const logBodyMetric = (payload: Record<string, unknown>) =>
  request("/logs/body-metric", { method: "POST", body: JSON.stringify(payload) });
