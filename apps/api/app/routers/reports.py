import re
import unicodedata
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.position_spec import PositionSpec
from app.services.candidate_evaluation_service import CandidateEvaluationService
from app.services.candidate_service import CandidateService
from app.services.comparison_report_service import ComparisonReportService
from app.services.report_service import ReportService

router = APIRouter(tags=["reportes"])


class ComparisonReportRequest(BaseModel):
    evaluation_ids: list[int] = Field(..., min_length=1, max_length=5)


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", no_accents).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "Sin_nombre"


def _build_filename(
    candidate_name: str,
    position_spec_title: str | None,
    evaluation_id: int,
    extension: str,
) -> str:
    """Genera 'Evaluacion_<Perfil>_<Nombre>_<Apellido>.ext' a partir de los datos."""
    perfil = _slug((position_spec_title or "PerfilObjetivo").replace("Perfil objetivo -", "").strip())
    nombre = _slug(candidate_name or f"Candidato_{evaluation_id}")
    return f"Evaluacion_{perfil}_{nombre}.{extension}"


def _resolve_filename(db: Session, evaluation_id: int, extension: str) -> str:
    evaluation = CandidateEvaluationService(db).get(evaluation_id)
    if evaluation is None:
        return f"Evaluacion_{evaluation_id}.{extension}"
    candidate = CandidateService(db).get(evaluation.candidate_id)
    position_spec = db.get(PositionSpec, evaluation.position_spec_id)
    return _build_filename(
        candidate_name=candidate.full_name if candidate else f"Candidato_{evaluation_id}",
        position_spec_title=position_spec.title if position_spec else None,
        evaluation_id=evaluation_id,
        extension=extension,
    )


@router.post("/api/evaluaciones/{evaluation_id}/reportes/word")
def generate_word_report(evaluation_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    evaluation_service = CandidateEvaluationService(db)
    evaluation = evaluation_service.get(evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada")

    report_service = ReportService(db)
    file_bytes = report_service.generate_word(evaluation)
    file_name = _resolve_filename(db, evaluation_id, "docx")
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post("/api/evaluaciones/{evaluation_id}/reportes/pdf")
def generate_pdf_report(evaluation_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    evaluation_service = CandidateEvaluationService(db)
    evaluation = evaluation_service.get(evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada")

    report_service = ReportService(db)
    file_bytes = report_service.generate_pdf(evaluation)
    file_name = _resolve_filename(db, evaluation_id, "pdf")
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/api/reportes/{evaluation_id}/download")
def download_report(
    evaluation_id: int,
    format: str = Query(default="pdf", pattern="^(pdf|word)$"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    if format == "word":
        return generate_word_report(evaluation_id=evaluation_id, db=db)
    return generate_pdf_report(evaluation_id=evaluation_id, db=db)


@router.post("/api/mandatos/{mandate_id}/reportes/comparacion")
def generate_comparison_pdf(
    mandate_id: int,
    payload: ComparisonReportRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    service = ComparisonReportService(db)
    try:
        file_bytes = service.generate_pdf(mandate_id, payload.evaluation_ids)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    file_name = f"Comparativo_Mandato_{mandate_id}_{len(payload.evaluation_ids)}_candidatos.pdf"
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
