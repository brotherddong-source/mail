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
  to_emails: { address: string; name: string }[];
  cc_emails: { address: string; name: string }[];
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

// ----------------------------------------------------------------
// 메일함 분류
// ----------------------------------------------------------------
export type Mailbox = "representative" | "institutional" | "personal";

const REPRESENTATIVE_EMAIL = "ip@ip-lab.co.kr";
const INSTITUTIONAL_EMAIL = "mail@ip-lab.co.kr";
const OUR_DOMAIN = "ip-lab.co.kr";

/** 메일이 어느 메일함에 속하는지 판별 */
export function classifyMailbox(mail: MailMessage): Mailbox {
  const allAddresses = [
    ...(mail.to_emails || []).map((e) => (e.address || "").toLowerCase()),
    ...(mail.cc_emails || []).map((e) => (e.address || "").toLowerCase()),
  ];
  // 발신 메일인 경우 from_email로도 판별
  const from = (mail.from_email || "").toLowerCase();
  if (from === REPRESENTATIVE_EMAIL || allAddresses.includes(REPRESENTATIVE_EMAIL)) {
    return "representative";
  }
  if (from === INSTITUTIONAL_EMAIL || allAddresses.includes(INSTITUTIONAL_EMAIL)) {
    return "institutional";
  }
  return "personal";
}

/** 발신자가 ip-lab.co.kr 도메인이면 발신 메일 */
export function isOutgoingMail(mail: MailMessage): boolean {
  return (mail.from_email || "").toLowerCase().endsWith(`@${OUR_DOMAIN}`);
}

export const MAILBOX_LABEL: Record<Mailbox, string> = {
  representative: "대표메일",
  institutional: "기관메일",
  personal: "개인메일",
};

export const MAILBOX_COLOR: Record<Mailbox, { bg: string; text: string; dot: string }> = {
  representative: { bg: "bg-indigo-50", text: "text-indigo-700", dot: "bg-indigo-500" },
  institutional: { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" },
  personal: { bg: "bg-gray-50", text: "text-gray-600", dot: "bg-gray-400" },
};

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

export interface Case {
  id: string;
  case_number: string;
  app_number: string | null;
  client_name: string;
  client_domain: string | null;
  country: string;
  case_type: string | null;
  status: string | null;
  deadline: string | null;
}

export interface UploadResult {
  status: string;
  created: number;
  updated: number;
  total: number;
  errors: { row: number; case_number: string; error: string }[];
}

// ----------------------------------------------------------------
// API Calls
// ----------------------------------------------------------------
export const mailApi = {
  list: (params?: { status?: string; search?: string }) =>
    api.get<MailMessage[]>("/api/mails", { params }).then((r) => r.data),
  detail: (id: string) =>
    api.get<MailDetail>(`/api/mails/${id}`).then((r) => r.data),
  approveDraft: (
    draftId: string,
    body: {
      edited_body?: string;
      use_ko?: boolean;
      edited_to?: { email: string; name?: string }[];
      edited_cc?: { email: string; name?: string }[];
    },
  ) => api.post(`/api/drafts/${draftId}/approve`, body).then((r) => r.data),
  rejectDraft: (draftId: string, reason: string) =>
    api.post(`/api/drafts/${draftId}/reject`, { reason }).then((r) => r.data),
  listTemplates: (mailId?: string) =>
    api.get<{ templates: TemplateItem[]; recommended_id: string | null }>(
      "/api/drafts/templates",
      { params: mailId ? { mail_id: mailId } : {} },
    ).then((r) => r.data),
  listSignatures: (senderEmail: string) =>
    api.get<{ signatures: SignatureItem[] }>(
      "/api/drafts/signatures",
      { params: { sender_email: senderEmail } },
    ).then((r) => r.data),
  regenerateDraft: (
    draftId: string,
    body: { template_id?: string; signature_id?: string; sender_email?: string },
  ) =>
    api.post<{ status: string; draft_ko: string; draft_en: string }>(
      `/api/drafts/${draftId}/regenerate`,
      body,
    ).then((r) => r.data),
};

export interface TemplateItem {
  id: string;
  name: string;
  category: string;
  language: "ko" | "en";
  use_case: string;
  subject_pattern: string;
  variables: string[];
  is_recommended: boolean;
}

export interface SignatureItem {
  id: string;
  label: string;
  language: "ko" | "en";
  sender_email: string;
  body: string;
  is_default: boolean;
}

// ----------------------------------------------------------------
// Signatures CRUD
// ----------------------------------------------------------------
export interface SignatureCreateBody {
  sender_email: string;
  label: string;
  language: "ko" | "en";
  body: string;
  is_default?: boolean;
}

export const signatureApi = {
  list: (senderEmail?: string) =>
    api.get<{ signatures: SignatureItem[] }>("/api/signatures", {
      params: senderEmail ? { sender_email: senderEmail } : {},
    }).then((r) => r.data),
  create: (body: SignatureCreateBody) =>
    api.post<SignatureItem>("/api/signatures", body).then((r) => r.data),
  update: (id: string, body: Partial<SignatureCreateBody>) =>
    api.put<SignatureItem>(`/api/signatures/${id}`, body).then((r) => r.data),
  delete: (id: string) =>
    api.delete(`/api/signatures/${id}`).then((r) => r.data),
  seed: () =>
    api.post<{ status: string; created: number }>("/api/signatures/seed").then((r) => r.data),
};

export const caseApi = {
  list: () => api.get<Case[]>("/api/cases").then((r) => r.data),
  uploadCases: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<UploadResult>("/api/cases/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
  uploadContacts: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<UploadResult>("/api/cases/upload-contacts", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
  downloadTemplate: () => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/cases/template`
    );
  },
};
