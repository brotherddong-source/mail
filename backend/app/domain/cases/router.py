"""
사건 관리 API
- 사건 목록 조회
- 고객 DB 엑셀 업로드 (연락처 임포트)
- 사건 엑셀 업로드 (사건 등록/수정)
- 엑셀 템플릿 다운로드
"""
import io
from datetime import date

import openpyxl
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.cases.models import Case, Party

router = APIRouter()


# ----------------------------------------------------------------
# 사건 목록 조회
# ----------------------------------------------------------------
@router.get("")
async def list_cases(db: AsyncSession = Depends(get_db), limit: int = 200):
    result = await db.execute(select(Case).order_by(Case.created_at.desc()).limit(limit))
    cases = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "case_number": c.case_number,
            "app_number": c.app_number,
            "client_name": c.client_name,
            "client_domain": c.client_domain,
            "country": c.country,
            "case_type": c.case_type,
            "status": c.status,
            "deadline": c.deadline.isoformat() if c.deadline else None,
        }
        for c in cases
    ]


# ----------------------------------------------------------------
# 고객 DB 업로드 (특허사무소 연락처 형식)
# ----------------------------------------------------------------
@router.post("/upload-contacts")
async def upload_contacts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    고객 DB 엑셀 업로드.
    컬럼: E-mail, 고객구분, 고객명, 고객명(영문), 국가, 특허고객번호, 회사명 등
    이메일이 있는 고객은 Party로 등록 → 메일 자동 매칭에 활용
    """
    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content), dtype=str, engine="xlrd" if file.filename.endswith(".xls") else "openpyxl")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {e}")

    df = df.where(pd.notna(df), None)
    created, updated, skipped = 0, 0, 0

    for _, row in df.iterrows():
        email = _str(row.get("E-mail"))
        name = _str(row.get("고객명"))
        name_en = _str(row.get("고객명(영문)"))
        company = _str(row.get("회사명"))
        role_raw = _str(row.get("고객구분")) or "client"

        # 이메일도 이름도 없으면 스킵
        if not email and not name:
            skipped += 1
            continue

        # 역할 매핑
        role = "client"
        if role_raw and "의뢰인" in role_raw:
            role = "client"
        elif role_raw and "대리인" in role_raw:
            role = "opponent_agent"

        # 이메일로 기존 Party 조회
        existing = None
        if email:
            result = await db.execute(
                select(Party).where(Party.email == email.lower())
            )
            existing = result.scalar_one_or_none()

        if existing:
            # 업데이트
            existing.name = name or existing.name
            existing.org_name = company or existing.org_name
            existing.role = role
            updated += 1
        else:
            # 신규 등록 (case_id 없는 독립 연락처)
            party = Party(
                name=name or name_en,
                email=email.lower() if email else None,
                role=role,
                org_name=company,
            )
            db.add(party)
            created += 1

    await db.commit()
    return {
        "status": "ok",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": created + updated,
    }


# ----------------------------------------------------------------
# 사건 DB 업로드
# ----------------------------------------------------------------
@router.post("/upload")
async def upload_cases(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    사건 DB 엑셀 업로드.
    필수 컬럼: 사건번호, 고객사명, 국가
    """
    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content), dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {e}")

    required = {"사건번호", "고객사명", "국가"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"필수 컬럼 없음: {missing}")

    df = df.where(pd.notna(df), None)
    created, updated, errors = 0, 0, []

    for idx, row in df.iterrows():
        case_number = _str(row.get("사건번호"))
        if not case_number:
            continue
        try:
            result = await db.execute(select(Case).where(Case.case_number == case_number))
            case = result.scalar_one_or_none()
            deadline = _parse_date(row.get("마감일"))

            if case:
                case.client_name = _str(row.get("고객사명")) or case.client_name
                case.client_domain = _str(row.get("고객도메인")) or case.client_domain
                case.country = _str(row.get("국가")) or case.country
                case.case_type = _str(row.get("사건유형")) or case.case_type
                case.status = _str(row.get("상태")) or case.status
                case.app_number = _str(row.get("출원번호")) or case.app_number
                if deadline:
                    case.deadline = deadline
                updated += 1
            else:
                case = Case(
                    case_number=case_number,
                    app_number=_str(row.get("출원번호")),
                    client_name=_str(row.get("고객사명")) or "-",
                    client_domain=_str(row.get("고객도메인")),
                    country=_str(row.get("국가")) or "-",
                    case_type=_str(row.get("사건유형")),
                    status=_str(row.get("상태")),
                    deadline=deadline,
                )
                db.add(case)
                created += 1
        except Exception as e:
            errors.append({"row": idx + 2, "error": str(e)})

    await db.commit()
    return {"status": "ok", "created": created, "updated": updated, "errors": errors}


# ----------------------------------------------------------------
# 엑셀 템플릿 다운로드 (사건 DB용)
# ----------------------------------------------------------------
@router.get("/template")
async def download_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "사건목록"
    headers = ["사건번호", "출원번호", "등록번호", "고객사명", "고객도메인", "국가", "사건유형", "상태", "마감일"]
    ws.append(headers)
    ws.append(["KR-2024-00001", "10-2024-0012345", "", "삼성전자", "samsung.com", "KR", "patent", "출원중", "2025-06-30"])

    from openpyxl.styles import Font, PatternFill
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2563EB")
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 15

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cases_template.xlsx"},
    )


def _str(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("nan", "none") else None


def _parse_date(val) -> date | None:
    if not val:
        return None
    try:
        return pd.to_datetime(str(val)).date()
    except Exception:
        return None
