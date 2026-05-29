from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate
from app.reporting.docx_report_generator import build_docx_report
from app.reporting.pdf_report_generator import build_pdf_report
from app.reporting.report_context_builder import build_report_context


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_context(self, evaluation: CandidateEvaluation) -> dict[str, object]:
        candidate = self.db.get(Candidate, evaluation.candidate_id)
        position_spec = self.db.get(PositionSpec, evaluation.position_spec_id)
        mandate = None
        if position_spec is not None:
            mandate = self.db.get(SearchMandate, position_spec.search_mandate_id)
        return build_report_context(evaluation=evaluation, candidate=candidate, position_spec=position_spec, mandate=mandate)

    def generate_word(self, evaluation: CandidateEvaluation) -> bytes:
        context = self._get_context(evaluation)
        return build_docx_report(context)

    def generate_pdf(self, evaluation: CandidateEvaluation) -> bytes:
        context = self._get_context(evaluation)
        return build_pdf_report(context)
