from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_profile import CandidateProfile
from app.models.position_spec import PositionSpec
from app.scoring.fit_score_engine import evaluate_candidate


class CandidateEvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, candidate_id: int, position_spec: PositionSpec) -> CandidateEvaluation:
        profile_query = (
            select(CandidateProfile)
            .where(CandidateProfile.candidate_id == candidate_id)
            .order_by(CandidateProfile.created_at.desc())
        )
        profile = self.db.scalars(profile_query).first()
        if profile is None:
            raise ValueError("El candidato no tiene perfil estructurado. Genera perfil desde el documento primero.")

        evaluation_payload = evaluate_candidate(profile=profile, spec=position_spec)
        item = CandidateEvaluation(
            candidate_id=candidate_id,
            position_spec_id=position_spec.id,
            total_score=int(evaluation_payload["total_score"]),
            score_category=str(evaluation_payload["score_category"]),
            recommendation=str(evaluation_payload["recommendation"]),
            executive_summary=str(evaluation_payload["executive_summary"]),
            dimension_scores=list(evaluation_payload["dimension_scores"]),
            critical_gaps=list(evaluation_payload["critical_gaps"]),
            strengths=list(evaluation_payload["strengths"]),
            weaknesses=list(evaluation_payload["weaknesses"]),
            risks=list(evaluation_payload["risks"]),
            interview_questions=list(evaluation_payload["interview_questions"]),
            supporting_evidence=list(evaluation_payload["supporting_evidence"]),
            final_verdict=str(evaluation_payload["final_verdict"]),
            evaluation_json=evaluation_payload,
            model_version=str(evaluation_payload["model_version"]),
            prompt_version=str(evaluation_payload["prompt_version"]),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get(self, evaluation_id: int) -> CandidateEvaluation | None:
        return self.db.get(CandidateEvaluation, evaluation_id)

    def list_all(self) -> list[CandidateEvaluation]:
        query = select(CandidateEvaluation).order_by(CandidateEvaluation.created_at.desc())
        return list(self.db.scalars(query).all())

    def list_by_candidate(self, candidate_id: int) -> list[CandidateEvaluation]:
        query = (
            select(CandidateEvaluation)
            .where(CandidateEvaluation.candidate_id == candidate_id)
            .order_by(CandidateEvaluation.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def list_by_position_spec(self, position_spec_id: int) -> list[CandidateEvaluation]:
        query = (
            select(CandidateEvaluation)
            .where(CandidateEvaluation.position_spec_id == position_spec_id)
            .order_by(CandidateEvaluation.created_at.desc())
        )
        return list(self.db.scalars(query).all())
