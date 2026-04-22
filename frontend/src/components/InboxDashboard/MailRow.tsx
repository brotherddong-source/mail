"use client";
import {
  MailMessage,
  classifyMailbox,
  isOutgoingMail,
  MAILBOX_LABEL,
  MAILBOX_COLOR,
} from "@/lib/api";
import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { clsx } from "clsx";

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-500",
};

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-gray-100 text-gray-500",
  analyzed: "bg-blue-100 text-blue-600",
  draft_ready: "bg-green-100 text-green-700",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "처리 중",
  analyzed: "분석 완료",
  draft_ready: "초안 준비",
};

interface Props {
  mail: MailMessage;
  selected: boolean;
  onClick: () => void;
}

/** to_emails / cc_emails 중 ip-lab 주소 추출 */
function getIpLabMember(mail: MailMessage): string | null {
  const all = [...(mail.to_emails || []), ...(mail.cc_emails || [])];
  const found = all.find((e) => (e.address || "").toLowerCase().endsWith("@ip-lab.co.kr"));
  if (!found) return null;
  // 이름이 있으면 이름, 없으면 @앞 부분만
  return found.name || found.address.split("@")[0];
}

export default function MailRow({ mail, selected, onClick }: Props) {
  const receivedAt = mail.received_at
    ? format(new Date(mail.received_at), "MM/dd HH:mm", { locale: ko })
    : "-";
  const outgoing = isOutgoingMail(mail);
  const mailbox = classifyMailbox(mail);
  const mbColor = MAILBOX_COLOR[mailbox];
  const ipLabMember = getIpLabMember(mail);

  return (
    <tr
      onClick={onClick}
      className={clsx(
        "cursor-pointer border-b transition-colors hover:bg-blue-50",
        selected && "bg-blue-50"
      )}
    >
      {/* 메일함 + 방향 */}
      <td className="px-2 py-3 text-center">
        <div className="flex flex-col items-center gap-0.5">
          <span className={clsx("rounded px-1.5 py-0.5 text-[9px] font-semibold leading-tight", mbColor.bg, mbColor.text)}>
            {MAILBOX_LABEL[mailbox].slice(0, 2)}
          </span>
          {outgoing ? (
            <span className="text-[9px] text-emerald-500 font-bold">발신</span>
          ) : (
            <span className="text-[9px] text-blue-500 font-bold">수신</span>
          )}
        </div>
      </td>
      <td className="whitespace-nowrap px-3 py-3 text-gray-500">{receivedAt}</td>
      <td className="px-3 py-3">
        <div className="font-medium text-gray-900 truncate max-w-[120px]">{mail.from_name || mail.from_email}</div>
        <div className="text-xs text-gray-400 truncate max-w-[120px]">{mail.from_email}</div>
      </td>
      {/* 담당자 (ip-lab 멤버) */}
      <td className="px-3 py-3">
        {ipLabMember ? (
          <span className="inline-block rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-medium text-indigo-700 truncate max-w-[80px]">
            {ipLabMember}
          </span>
        ) : outgoing ? (
          <span className="text-[10px] text-gray-300">발신</span>
        ) : (
          <span className="text-[10px] text-gray-300">-</span>
        )}
      </td>
      <td className="px-3 py-3">
        {mail.case_number ? (
          <div>
            <div className="text-xs font-mono text-blue-700">{mail.case_number}</div>
            <div className="text-xs text-gray-400 truncate max-w-[100px]">{mail.client_name}</div>
          </div>
        ) : (
          <span className="text-xs text-gray-300">미매칭</span>
        )}
      </td>
      <td className="px-3 py-3 max-w-[200px]">
        <p className="text-xs text-gray-600 line-clamp-2">{mail.ai_summary || mail.subject}</p>
      </td>
      <td className="px-3 py-3 text-center">
        {mail.requires_reply ? (
          <span className="inline-block h-2 w-2 rounded-full bg-orange-400" title="회신 필요" />
        ) : (
          <span className="inline-block h-2 w-2 rounded-full bg-gray-200" />
        )}
      </td>
      <td className="px-3 py-3 text-center">
        {mail.priority && (
          <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium", PRIORITY_BADGE[mail.priority])}>
            {mail.priority === "high" ? "긴급" : mail.priority === "medium" ? "보통" : "낮음"}
          </span>
        )}
      </td>
      <td className="px-3 py-3 text-center">
        <span className={clsx("rounded-full px-2 py-0.5 text-xs", STATUS_BADGE[mail.processing_status] || "bg-gray-100 text-gray-400")}>
          {STATUS_LABEL[mail.processing_status] || mail.processing_status}
        </span>
      </td>
    </tr>
  );
}
