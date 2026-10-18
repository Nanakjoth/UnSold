/** Calls the auth API. Token is attached automatically by apiFetch. */

import { apiFetch, clearToken, setToken } from "./api";
import type { DeleteSummary, SessionResponse, SessionUpdate } from "../types/api";

interface DemoLoginResponse {
  token: string;
  uid: string;
  pseudonym: string;
  label: string;
  notice: string;
}

/**
 * Demo-mode identity bootstrap. `label` picks which demo identity to mint
 * (e.g. "a", "b") so multi-member flows can be exercised locally. In
 * production this is replaced by Firebase anonymous auth; the server-side
 * ownership checks are identical either way.
 */
export async function demoLogin(label = "default"): Promise<SessionResponse> {
  const login = await apiFetch<DemoLoginResponse>("/api/dev/demo-login", {
    method: "POST",
    body: JSON.stringify({ label }),
  });
  setToken(login.token);
  return getSession();
}

/** Get-or-create the caller's pseudonymous session. */
export function getSession(): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/api/auth/session", { method: "POST" });
}

export function updateSession(update: SessionUpdate): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/api/auth/session", {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}

/** Delete every record owned by the caller, then drop the local token. */
export async function deleteMyData(): Promise<DeleteSummary> {
  const summary = await apiFetch<DeleteSummary>("/api/auth/session", {
    method: "DELETE",
  });
  clearToken();
  return summary;
}

export function signOut(): void {
  clearToken();
}
