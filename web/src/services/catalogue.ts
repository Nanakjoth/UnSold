/** Catalogue browse/search/detail + saved/feedback calls. */

import { apiFetch } from "./api";
import type {
  CategoryListResponse,
  FeedbackAction,
  FeedbackReason,
  FeedbackResponse,
  InterestDetail,
  InterestListResponse,
  SavedListResponse,
} from "../types/api";

export interface InterestQuery {
  q?: string;
  category?: string[];
  beginner?: boolean;
  mode?: string;
  tag?: string[];
  limit?: number;
  offset?: number;
}

/** Keyword search + filters over the sample catalogue (no auth required). */
export function listInterests(query: InterestQuery = {}): Promise<InterestListResponse> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  for (const category of query.category ?? []) params.append("category", category);
  if (query.beginner !== undefined) params.set("beginner", String(query.beginner));
  if (query.mode) params.set("mode", query.mode);
  for (const tag of query.tag ?? []) params.append("tag", tag);
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  if (query.offset !== undefined) params.set("offset", String(query.offset));
  const qs = params.toString();
  return apiFetch<InterestListResponse>(`/api/interests${qs ? `?${qs}` : ""}`);
}

/** Category facet counts (drives the filter chips). */
export function listCategories(): Promise<CategoryListResponse> {
  return apiFetch<CategoryListResponse>("/api/interests/categories");
}

/** Full entry with expanded, labelled relationships. */
export function getInterest(slug: string): Promise<InterestDetail> {
  return apiFetch<InterestDetail>(`/api/interests/${encodeURIComponent(slug)}`);
}

// --- Saved -----------------------------------------------------------------

export function listSaved(): Promise<SavedListResponse> {
  return apiFetch<SavedListResponse>("/api/library/saved");
}

export function saveInterest(slug: string): Promise<SavedListResponse> {
  return apiFetch<SavedListResponse>(`/api/library/saved/${encodeURIComponent(slug)}`, {
    method: "POST",
  });
}

export function unsaveInterest(slug: string): Promise<SavedListResponse> {
  return apiFetch<SavedListResponse>(`/api/library/saved/${encodeURIComponent(slug)}`, {
    method: "DELETE",
  });
}

// --- Feedback --------------------------------------------------------------

export function sendFeedback(
  interestSlug: string,
  action: FeedbackAction,
  reason?: FeedbackReason,
): Promise<FeedbackResponse> {
  return apiFetch<FeedbackResponse>("/api/library/feedback", {
    method: "POST",
    body: JSON.stringify({ interest_slug: interestSlug, action, reason }),
  });
}
