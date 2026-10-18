/** Types mirroring the backend Pydantic schemas (Stage 1). */

export interface AppConfig {
  app_mode: "demo" | "production";
  demo: boolean;
  ai_available: boolean;
  notice: string | null;
}

export interface SessionResponse {
  uid: string;
  pseudonym: string;
  language: string;
  is_synthetic: boolean;
  created_at: string;
}

export interface SessionUpdate {
  language?: string | null;
}

export interface DeleteSummary {
  deleted: Record<string, number>;
  total: number;
}

export interface ApiErrorBody {
  error: { code: string; message: string };
}

// --- Catalogue ---------------------------------------------------------------

export type Difficulty = "beginner" | "intermediate";
export type SoloOrGroup = "solo" | "group";
export type OnlineOrInPerson = "online" | "in_person";

export type RelationshipType =
  | "shares_material"
  | "shares_technique"
  | "shares_skill"
  | "shares_way_of_thinking"
  | "related_culture_or_context"
  | "complementary_activity"
  | "prerequisite_for"
  | "contrasts_with";

export interface InterestCard {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  category: string;
  tags: string[];
  time_commitment: string | null;
  difficulty: Difficulty | null;
  solo_or_group: SoloOrGroup[];
  online_or_in_person: OnlineOrInPerson[];
  is_sample_content: boolean;
}

export interface RelatedInterest {
  type: RelationshipType;
  note: string | null;
  interest: InterestCard;
}

export interface InterestDetail extends InterestCard {
  long_description: string;
  beginner_step: string;
  skills: string[];
  materials: string[];
  ways_of_thinking: string[];
  accessibility_notes: string[];
  languages: string[];
  source_notes: string | null;
  related: RelatedInterest[];
}

export interface InterestListResponse {
  items: InterestCard[];
  total: number;
  limit: number;
  offset: number;
  search_source: "keyword";
  ai_search_available: boolean;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface CategoryListResponse {
  items: CategoryCount[];
}

// --- Saved & feedback --------------------------------------------------------

export type FeedbackAction = "save" | "dismiss" | "already_know" | "want_to_try";
export type FeedbackReason = "too_similar" | "not_relevant" | "not_accessible";

export interface SavedListResponse {
  items: InterestCard[];
  total: number;
}

export interface AgreementSummary {
  share_matching: number;
  sample_size: number;
  label: string;
}

export interface FeedbackResponse {
  interest_slug: string;
  action: FeedbackAction;
  agreement: AgreementSummary | null;
}

// --- Advice core -------------------------------------------------------------

export type GoalType =
  | "explore_options"
  | "make_a_decision"
  | "career_switch"
  | "grow_in_role"
  | "negotiate"
  | "handle_setback"
  | "avoid_pitfall"
  | "learn_skill";

export type DistressLevel = "none" | "mild" | "moderate" | "high";

export type RiskFlag =
  | "money_involved"
  | "urgency"
  | "health_related"
  | "legal_related"
  | "off_platform_request"
  | "financial_loss_imminent";

export type ExperienceBand = "5-10 years" | "10-15 years" | "15-20 years" | "20+ years";
export type MatchType = "DIRECT" | "CROSS_DOMAIN";

export interface NeedIntent {
  short_summary: string;
  domains: string[];
  goal_type: GoalType;
  decision_pending: boolean;
  money_involved: boolean;
  preferred_mentor_traits: string[];
  language: string;
  distress_level: DistressLevel;
  risk_flags: RiskFlag[];
}

export interface ClarifyingQuestion {
  question: string;
  why: string;
}

export interface NeedInterpretation {
  summary: string;
  intent: NeedIntent;
  clarifying_questions: ClarifyingQuestion[];
  interpretation_source: "gemini" | "fallback";
}

export interface MentorPublicCard {
  role_band: string;
  seniority_band: ExperienceBand;
  domains: string[];
  industries: string[];
  languages: string[];
  country_code: string;
  topics_offered: string[];
  bio_public: string;
  slot_lengths_min: number[];
}

export interface MentorCard {
  id: string;
  pseudonym: string;
  is_synthetic: boolean;
  public_card: MentorPublicCard;
}

export interface MentorListResponse {
  items: MentorCard[];
  total: number;
  retrieval_source: "keyword" | "gemini";
}

export interface WatchOut {
  note: string;
}

export interface MentorMatch {
  mentor: MentorCard;
  fit_score: number;
  match_type: MatchType;
  explanation: string;
  cross_domain_value: string | null;
  watch_outs: WatchOut[];
  starter_questions: string[];
}

export interface NeedCreate {
  text: string;
  category?: string | null;
  language?: string;
  money_involved?: boolean;
}

export interface NeedMatchesResponse {
  need_id: string;
  interpretation: NeedInterpretation;
  matches: MentorMatch[];
  no_strong_match: boolean;
  retrieval_source: "keyword" | "gemini";
  notice: string | null;
}

// --- Sample scenarios (spec §14 demo seed data) -----------------------------

export interface SampleScenario {
  id: string;
  text: string;
  domain: string;
  money_involved: boolean;
  intended_mentor_id: string;
  is_sample_content: boolean;
}

// --- Stage A2: Guardian, sessions, Friend Test ------------------------------

export type GuardianCategory =
  | "NONE"
  | "DIRECT_PROMO"
  | "CONTACT_SOLICIT"
  | "URGENCY_FEAR"
  | "SOFT_STEERING"
  | "AFFILIATE_REFERRAL";

export type GuardianAction = "ALLOW" | "WARN" | "BLOCK_AND_REDACT";

export type MoneyStance = "n/a" | "pushes_to_spend" | "neutral" | "cautions_against_spending";

export type SessionStatus = "REQUESTED" | "ACTIVE" | "ENDED" | "CANCELLED";
export type SenderRole = "mentee" | "mentor";

export interface GuardianSafety {
  distress: DistressLevel;
  risk_flags: string[];
}

export interface GuardianVerdict {
  is_pitch: boolean;
  category: GuardianCategory;
  severity: number;
  evidence_span: string;
  reason: string;
  money_stance: MoneyStance;
  rule_hits: string[];
  safety: GuardianSafety;
  source: "gemini" | "rules" | "fallback";
}

export interface GuardianDecision {
  action: GuardianAction;
  final_severity: number;
  strike_incurred: boolean;
  ends_session: boolean;
  display_text: string;
  tag: string | null;
}

export interface GuardianSummary {
  messages_checked: number;
  max_severity: number;
  strikes: number;
  pitches_flagged: number;
}

export interface SessionMessage {
  id: string;
  session_id: string;
  seq: number;
  sender_role: SenderRole;
  text_scrubbed: string;
  display_text: string;
  is_simulated: boolean;
  guardian: GuardianVerdict;
  action: GuardianAction;
  created_at: string;
}

export interface SessionMessageResponse {
  message: SessionMessage;
  guardian: GuardianDecision;
}

export interface Session {
  id: string;
  mentee_id: string;
  mentor_id: string;
  mentor_pseudonym: string;
  need_id: string | null;
  intent_summary: string | null;
  status: SessionStatus;
  money_involved: boolean;
  guardian: GuardianSummary;
  money_stance: MoneyStance;
  reveal: { mentee_consent: boolean; mentor_consent: boolean; revealed_at: string | null };
  is_synthetic: boolean;
  created_at: string;
  ended_at: string | null;
}

export interface SessionListResponse {
  items: Session[];
  total: number;
}

export interface MessageListResponse {
  items: SessionMessage[];
  total: number;
}

export interface FriendTestResult {
  applicable: boolean;
  stance: MoneyStance;
  label: string;
  is_simulated: boolean;
}

// --- Stage A3: reveal, summary, feedback, metrics ---------------------------

export type RevealState = "NONE" | "ONE_SIDED" | "REVEALED";

export interface RevealContact {
  role: SenderRole;
  display_name: string;
  contact_optional: string | null;
  is_simulated: boolean;
}

export interface RevealResponse {
  state: RevealState;
  revealed: boolean;
  contacts: RevealContact[];
  notice: string | null;
}

export interface SummaryThingToTry {
  slug: string;
  title: string;
  short_description: string;
  category: string;
}

export interface SessionSummary {
  key_points: string[];
  action_items: string[];
  caveats: string[];
  things_to_try: SummaryThingToTry[];
  source: "gemini" | "fallback";
  edited: boolean;
}

export type FeltPitched = "yes" | "no" | "unsure";

export interface AgreementMetric {
  share: number | null;
  sample_size: number;
  label: string;
  is_simulated: boolean;
  guardian_flagged: number;
  mentee_reported_pitch: number;
}

export interface SessionFeedbackResponse {
  ok: boolean;
  agreement: AgreementMetric | null;
}

export type FeedbackBody =
  | {
      role: "mentee";
      mentee: {
        helpfulness_1_5: number;
        felt_pitched: FeltPitched;
        would_recommend: boolean;
        free_text?: string;
      };
    }
  | {
      role: "mentor";
      mentor: {
        mentee_seriousness_1_5: number;
        respectful: boolean;
        free_text?: string;
      };
    };

// --- UI redesign: public trust surfaces --------------------------------------

/** POST /api/guardian/try — the anonymous, zero-persistence playground. */
export interface GuardianTryResponse {
  action: GuardianAction;
  severity: number;
  categories: string[];
  is_pitch: boolean;
  display_text: string;
  scrubbed: boolean;
  source: "gemini" | "rules" | "fallback";
  notice: string;
}

/** GET /api/public/stats — aggregates only, never any user content. */
export interface PublicStats {
  mentors: { count: number; all_synthetic: boolean };
  guardian_eval: {
    total_labels: number;
    labels_reviewed: number;
    accuracy_claimed: boolean;
    test: {
      precision: number;
      recall: number;
      f1: number;
      hard_negative_fpr: number | null;
    } | null;
    run_at: string | null;
  } | null;
  agreement: { shown: boolean; samples: number; share: number | null } | null;
  notice: string;
}

// --- Stage P3: offline evaluation (spec §12) ---------------------------------

export interface EvalRun {
  run_id: string;
  created_at?: string;
  n: number;
  split: string;
  precision: number;
  recall: number;
  f1: number;
  hard_negative_fpr: number | null;
  hard_negative_count: number;
  per_category_recall: Record<string, number>;
  per_category_support: Record<string, number>;
  confusion: Record<string, Record<string, number>>;
  false_positives: Array<Record<string, unknown>>;
  false_negatives: Array<Record<string, unknown>>;
  review_status: string;
  model: string;
  prompt_version: string;
}
