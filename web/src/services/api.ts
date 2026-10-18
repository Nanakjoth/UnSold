import type { ApiErrorBody, AppConfig } from "../types/api";

/** Used when the API is unreachable — demo is the safe, honest fallback. */
const FALLBACK: AppConfig = {
  app_mode: "demo",
  demo: true,
  ai_available: false,
  notice: "Prototype using synthetic data.",
};

/** Error carrying the API's `{ code, message }` envelope. */
export class ApiRequestError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

// --- Demo bearer token storage ---------------------------------------------
// In production this is replaced by a Firebase ID token obtained from
// Firebase anonymous auth. In demo mode the API mints a short-lived signed
// token via POST /api/dev/demo-login. Either way the server verifies it and
// derives the uid — the client never chooses its own identity.

const TOKEN_KEY = "atlas.demo.token";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* storage unavailable; session just won't persist across reloads */
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

/** Authenticated JSON request. Throws `ApiRequestError` on a non-2xx response. */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(path, { ...options, headers });

  if (!response.ok) {
    let code = "unknown";
    let message = `Request failed (${response.status}).`;
    try {
      const body = (await response.json()) as Partial<ApiErrorBody>;
      if (body.error) {
        code = body.error.code;
        message = body.error.message;
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiRequestError(response.status, code, message);
  }

  return (await response.json()) as T;
}

/** Public, non-sensitive runtime flags. Never requires a token. */
export async function fetchConfig(): Promise<AppConfig> {
  try {
    const response = await fetch("/api/config");
    return response.ok ? ((await response.json()) as AppConfig) : FALLBACK;
  } catch {
    return FALLBACK;
  }
}
