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

  listConversations: () => authed<Conversation[]>("/conversations"),

  createConversation: () =>
    authed<Conversation>("/conversations", { method: "POST" }),

  getMessages: (convId: string) =>
    authed<ChatMessage[]>(`/conversations/${convId}/messages`),

  deleteConversation: (convId: string) =>
    fetch(`${BASE}/conversations/${convId}`, { method: "DELETE", headers: authHeader() }),
};

export type Conversation = { id: string; title: string; created_at: string };

export type Citation = { title: string; source: string; url: string | null; snippet: string };

export type ChatMessage = {
  id: string;
  role: string;
  content: string;
  citations: Citation[];
  created_at: string;
};

export type RoadmapItem = {
  skill: string;
  milestone: number;
  est_hours: number;
  importance: number;
  why: string;
};

export type RoadmapEvent = {
  role: string;
  version: number;
  total_hours: number;
  items: RoadmapItem[];
};

export type StreamHandlers = {
  onStep?: (data: Record<string, unknown>) => void;
  onToken?: (t: string) => void;
  onCitation?: (c: Citation) => void;
  onRoadmap?: (r: RoadmapEvent) => void;
  onDone?: (data: Record<string, unknown>) => void;
  onError?: (err: string) => void;
};

// Stream a chat message over SSE (fetch + ReadableStream; EventSource is GET-only).
export async function streamMessage(
  convId: string,
  content: string,
  h: StreamHandlers,
): Promise<void> {
  const res = await fetch(`${BASE}/conversations/${convId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ content }),
  });
  if (!res.ok || !res.body) {
    h.onError?.(`Request failed (${res.status})`);
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const eventLine = block.split("\n").find((l) => l.startsWith("event: "));
      const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.slice(7).trim();
      const data = JSON.parse(dataLine.slice(6));
      if (event === "token") h.onToken?.(data.t);
      else if (event === "citation") h.onCitation?.(data);
      else if (event === "roadmap") h.onRoadmap?.(data);
      else if (event === "agent_step") h.onStep?.(data);
      else if (event === "done") h.onDone?.(data);
    }
  }
}

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
