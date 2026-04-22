"""
서명 관리 API
- 목록 조회 (발신자별)
- 생성 / 수정 / 삭제
- 전체 직원 시드 (최초 1회 실행)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.signatures.models import Signature

router = APIRouter()


class SignatureCreate(BaseModel):
    sender_email: str
    label: str
    language: str = "ko"
    body: str
    is_default: bool = False


class SignatureUpdate(BaseModel):
    label: str | None = None
    language: str | None = None
    body: str | None = None
    is_default: bool | None = None


def _sig_dict(s: Signature) -> dict:
    return {
        "id": str(s.id),
        "sender_email": s.sender_email,
        "label": s.label,
        "language": s.language,
        "body": s.body,
        "is_default": s.is_default,
    }


# ── 목록 ─────────────────────────────────────────────────────────
@router.get("")
async def list_signatures(
    sender_email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Signature).order_by(Signature.is_default.desc(), Signature.label)
    if sender_email:
        q = q.where(Signature.sender_email == sender_email.lower())
    result = await db.execute(q)
    sigs = result.scalars().all()

    # DB에 없으면 하드코딩 생성 데이터로 폴백
    if not sigs and sender_email:
        from app.templates.signatures import get_signatures_for_user
        return {"signatures": get_signatures_for_user(sender_email)}

    return {"signatures": [_sig_dict(s) for s in sigs]}


# ── 생성 ─────────────────────────────────────────────────────────
@router.post("")
async def create_signature(
    body: SignatureCreate,
    db: AsyncSession = Depends(get_db),
):
    sig = Signature(
        sender_email=body.sender_email.lower(),
        label=body.label,
        language=body.language,
        body=body.body,
        is_default=body.is_default,
    )
    db.add(sig)
    await db.commit()
    await db.refresh(sig)
    return _sig_dict(sig)


# ── 수정 ─────────────────────────────────────────────────────────
@router.put("/{sig_id}")
async def update_signature(
    sig_id: uuid.UUID,
    body: SignatureUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Signature).where(Signature.id == sig_id))
    sig = result.scalar_one_or_none()
    if not sig:
        raise HTTPException(status_code=404, detail="서명을 찾을 수 없습니다.")
    if body.label is not None:
        sig.label = body.label
    if body.language is not None:
        sig.language = body.language
    if body.body is not None:
        sig.body = body.body
    if body.is_default is not None:
        sig.is_default = body.is_default
    await db.commit()
    return _sig_dict(sig)


# ── 삭제 ─────────────────────────────────────────────────────────
@router.delete("/{sig_id}")
async def delete_signature(
    sig_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(Signature).where(Signature.id == sig_id))
    await db.commit()
    return {"status": "deleted"}


# ── 전체 시드 (최초 1회) ─────────────────────────────────────────
@router.post("/seed")
async def seed_signatures(db: AsyncSession = Depends(get_db)):
    """
    signatures.py 하드코딩 데이터를 DB에 삽입.
    이미 있는 sender_email 은 건너뜀.
    """
    from app.templates.signatures import get_signatures_for_user, _PARTNERS, _STAFF_META  # noqa

    all_emails = list(_PARTNERS.keys()) + list(_STAFF_META.keys())
    created = 0

    for email in all_emails:
        # 이미 DB에 있으면 스킵
        existing = await db.execute(
            select(Signature).where(Signature.sender_email == email).limit(1)
        )
        if existing.scalar_one_or_none():
            continue

        for item in get_signatures_for_user(email):
            db.add(Signature(
                sender_email=email,
                label=item["label"],
                language=item["language"],
                body=item["body"],
                is_default=item["is_default"],
            ))
            created += 1

    await db.commit()
    return {"status": "ok", "created": created}
