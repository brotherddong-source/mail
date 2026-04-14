import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ----------------------------------------------------------------
// Types
// ----------------------------------------------------------------
export interface MailMessage {
  id: string;
  graph_message_id: string;
  from_email: string;
  from_name: string;
  subject: string;
  received_at: string;
  has_attachments: boolean;
  case_id: string | null;
  case_number: string | null;
  client_name: string | null;
  requires_reply: boolean | null;
  priority: "low" | "medium" | "high" | null;
  ai_summary: string | null;
  ai_classification: string | null;
  processing_status: string;
}

export interface MailDetail extends MailMessage {
  body_text: string | null;
  body_html: string | null;
  ai_translation: string | null;
  to_emails: { address: string; name: string }[];
  cc_emails: { address: string; name: string }[];
  drafts: DraftResponse[];
}

export interface DraftResponse {
  id: string;
  generated_body_ko: string | null;
  generated_body_en: string | null;
  reviewer_body: string | null;
  suggested_to: Recipient[];
  suggested_cc: Recipient[];
  approval_status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface Recipient {
  email: string;
  name?: string;
  role: string;
  reason: string;
}

// ----------------------------------------------------------------
// API Calls
// ----------------------------------------------------------------
export const mailApi = {
  list: (params?: { date?: string; status?: string }) =>
    api.get<MailMessage[]>("/api/mails", { params }).then((r) => r.data),

  detail: (id: string) =>
    api.get<MailDetail>(`/api/mails/${id}`).then((r) => r.data),

  approveDraft: (draftId: string, body: { edited_body?: string; use_ko?: boolean }) =>
    api.post(`/api/drafts/${draftId}/approve`, body).then((r) => r.data),

  rejectDraft: (draftId: string, reason: string) =>
    api.post(`/api/drafts/${draftId}/reject`, { reason }).then((r) => r.data),
};
