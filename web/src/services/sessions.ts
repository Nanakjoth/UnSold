/** Stage A2 calls: sessions, message sending, mentor replies, Friend Test. */

import { apiFetch } from "./api";
import type {
  AgreementMetric,
  EvalRun,
  FeedbackBody,
  FriendTestResult,
  MessageListResponse,
  RevealResponse,
  Session,
  SessionFeedbackResponse,
  SessionListResponse,
  SessionMessageResponse,
  SessionSummary,
} from "../types/api";

/** Open a session with a mentor (optionally linked to a prior need). */
export function createSession(body: { mentor_id: string; need_id?: string }): Promise<Session> {
  return apiFetch<Session>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** The caller's sessions, newest first. */
export function listSessions(): Promise<SessionListResponse> {
  return apiFetch<SessionListResponse>("/api/sessions");
}

export function getSession(sessionId: string): Promise<Session> {
  return apiFetch<Session>(`/api/sessions/${encodeURIComponent(sessionId)}`);
}

export function listMessages(sessionId: string): Promise<MessageListResponse> {
  return apiFetch<MessageListResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/messages`);
}

/** Send a mentee message. Returns the Guardian's decision alongside it. */
export function sendMessage(sessionId: string, text: string): Promise<SessionMessageResponse> {
  return apiFetch<SessionMessageResponse>(
    `/api/sessions/${encodeURIComponent(sessionId)}/messages`,
    { method: "POST", body: JSON.stringify({ text }) },
  );
}

/**
 * Generate the synthetic mentor's reply and screen it too.
 *
 * `style` selects the simulator's voice (honest/salesy/subtle) — a demo lever
 * for exercising the Guardian, not a user-facing feature. Honest default.
 */
export function requestMentorReply(
  sessionId: string,
  style: "honest" | "salesy" | "subtle" = "honest",
): Promise<SessionMessageResponse> {
  return apiFetch<SessionMessageResponse>(
    `/api/sessions/${encodeURIComponent(sessionId)}/mentor-reply?style=${style}`,
    { method: "POST" },
  );
}

export function endSession(sessionId: string): Promise<Session> {
  return apiFetch<Session>(`/api/sessions/${encodeURIComponent(sessionId)}/end`, {
    method: "POST",
  });
}

/** Friend Test: did the mentor push spending, caution it, or stay neutral? */
export function getFriendTest(sessionId: string): Promise<FriendTestResult> {
  return apiFetch<FriendTestResult>(`/api/sessions/${encodeURIComponent(sessionId)}/friend-test`);
}

// --- Stage A3: reveal, summary, feedback, metrics ---------------------------

/**
 * Mutual-consent reveal (spec 8). `consent=false` withdraws (only before
 * REVEALED). Returns the reveal state + contacts when (only when) REVEALED.
 */
export function setReveal(
  sessionId: string,
  consent: boolean,
  contactOptional?: string,
): Promise<RevealResponse> {
  return apiFetch<RevealResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/reveal`, {
    method: "POST",
    body: JSON.stringify({ consent, contact_optional: contactOptional }),
  });
}

/** The editable mentee-only summary, generated once the session ends. */
export function getSummary(sessionId: string): Promise<SessionSummary> {
  return apiFetch<SessionSummary>(`/api/sessions/${encodeURIComponent(sessionId)}/summary`);
}

/** Apply the mentee's edits. Any subset may be provided. */
export function editSummary(
  sessionId: string,
  body: { key_points?: string[]; action_items?: string[]; caveats?: string[] },
): Promise<SessionSummary> {
  return apiFetch<SessionSummary>(`/api/sessions/${encodeURIComponent(sessionId)}/summary`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

/** Feedback from either side. The mentee path returns the agreement metric. */
export function submitFeedback(
  sessionId: string,
  body: FeedbackBody,
): Promise<SessionFeedbackResponse> {
  return apiFetch<SessionFeedbackResponse>(
    `/api/sessions/${encodeURIComponent(sessionId)}/feedback`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

/** Guardian-vs-mentee agreement metric (demo-only route in this prototype). */
export function getGuardianMetrics(): Promise<{ agreement: AgreementMetric; notice?: string }> {
  return apiFetch("/api/dev/metrics/guardian");
}

/** The last offline Guardian evaluation run (spec §12). Demo-only route. */
export function getEvalRun(): Promise<{ run: EvalRun; notice?: string }> {
  return apiFetch("/api/dev/metrics/eval");
}
