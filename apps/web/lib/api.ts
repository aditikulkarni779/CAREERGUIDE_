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

export type Profile = {
  id: string;
  user_id: string;
  weekly_hours: number | null;
  career_goal: string | null;
  interests: string[] | null;
  target_companies: string[] | null;
  twin_version: number;
};

export type Readiness = {
  overall: number;
  components: Record<string, number | null>;
  target_role_slug: string | null;
  computed_at: string;
};

export type UserSkill = {
  skill_id: string;
  name: string;
  slug: string;
  category: string;
  proficiency: number;
  source: string;
};

export type OnboardingPayload = {
  education?: unknown[];
  learning_style?: string;
  weekly_hours?: number;
  target_companies?: string[];
  expected_salary?: number;
  interests?: string[];
  career_goal?: string;
  languages?: string[];
  frameworks?: string[];
  skills?: { name: string; proficiency: number }[];
  github_username?: string;
};

export type OnboardingResult = {
  profile_id: string;
  readiness: Readiness;
  added_skills: string[];
  skipped_skills: string[];
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

function authHeader(): Record<string, string> {
  const token = typeof window === "undefined" ? null : localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authed<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, headers: { ...authHeader(), ...(init?.headers ?? {}) } });
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

  getProfile: () => authed<Profile>("/profile"),

  onboarding: (payload: OnboardingPayload) =>
    authed<OnboardingResult>("/profile/onboarding", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getReadiness: () => authed<Readiness>("/profile/readiness"),

  getSkills: () => authed<UserSkill[]>("/profile/skills"),
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
