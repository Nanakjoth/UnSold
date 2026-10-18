/** Advice-core calls: interpret a need, and browse the mentor directory. */

import { apiFetch } from "./api";
import type { MentorCard, MentorListResponse, NeedCreate, NeedMatchesResponse, SampleScenario, GuardianTryResponse, PublicStats } from "../types/api";

/** Describe a situation and get an interpretation + grounded matches (auth). */
export function createNeed(body: NeedCreate): Promise<NeedMatchesResponse> {
  return apiFetch<NeedMatchesResponse>("/api/needs", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** Public sample situations for the advice front door (no account). */
export function listScenarios(): Promise<SampleScenario[]> {
  return apiFetch<SampleScenario[]>("/api/needs/scenarios");
}

/** Public mentor directory. No account required. */
export function listMentors(query: { domain?: string; language?: string; limit?: number } = {}): Promise<MentorListResponse> {
  const params = new URLSearchParams();
  if (query.domain) params.set("domain", query.domain);
  if (query.language) params.set("language", query.language);
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  const qs = params.toString();
  return apiFetch<MentorListResponse>(`/api/mentors${qs ? `?${qs}` : ""}`);
}

/** One mentor's public card. */
export function getMentor(mentorId: string): Promise<MentorCard> {
  return apiFetch<MentorCard>(`/api/mentors/${encodeURIComponent(mentorId)}`);
}

/** POST /api/guardian/try — see what the Guardian would do to a message.
 * Anonymous, rate-limited, and nothing you type is stored or logged. */
export function guardianTry(text: string): Promise<GuardianTryResponse> {
  return apiFetch<GuardianTryResponse>("/api/guardian/try", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

/** GET /api/public/stats — honest aggregate numbers for the Trust page. */
export function getPublicStats(): Promise<PublicStats> {
  return apiFetch<PublicStats>("/api/public/stats");
}
