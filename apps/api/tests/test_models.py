from app.db.base import Base
from app.models import (
    Candidate,
    CandidateDocument,
    CandidateEvaluation,
    CandidateProfile,
    PositionSpec,
    SearchMandate,
)


def test_search_mandate_table_registered() -> None:
    assert SearchMandate.__tablename__ in Base.metadata.tables


def test_new_domain_tables_registered() -> None:
    for table_name in [
        PositionSpec.__tablename__,
        Candidate.__tablename__,
        CandidateDocument.__tablename__,
        CandidateProfile.__tablename__,
        CandidateEvaluation.__tablename__,
    ]:
        assert table_name in Base.metadata.tables
