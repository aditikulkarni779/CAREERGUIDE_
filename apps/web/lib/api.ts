// Minimal API client for the FastAPI backend.
// Token stored in localStorage for MVP; move to httpOnly cookie in a later phase.

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type User = {
  id: string;
  email: string;
  role: string;
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const problem = await res.json().catch(() => ({}));
    throw new Error(problem.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenPair>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (accessToken: string) =>
    request<User>("/auth/me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
};

export const tokenStore = {
  save: (t: TokenPair) => {
    localStorage.setItem("access_token", t.access_token);
    localStorage.setItem("refresh_token", t.refresh_token);
  },
  access: () => (typeof window === "undefined" ? null : localStorage.getItem("access_token")),
  clear: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
};
