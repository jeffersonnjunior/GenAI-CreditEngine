from pathlib import Path

import pytest

from credit_engine.clients.bureau.stub import UnavailableBureauClient
from credit_engine.core.common.enums.proposal import ProposalStatus
from credit_engine.core.common.enums.risk import RiskBand
from credit_engine.models.proposal import ProposalCreate
from credit_engine.rag.chunking import (
    chunk_markdown_sections,
    load_policy_chunks,
    split_into_sentences,
    window_chunks,
)
from credit_engine.rag.embeddings import HashingEmbeddingFunction
from credit_engine.rag.lexical import lexical_overlap_score, rank_ids_by_lexical
from credit_engine.rag.retrieve import (
    build_retrieval_query,
    retrieve_compliance_excerpts,
)
from credit_engine.rag.rrf import reciprocal_rank_fusion
from credit_engine.rag.store import ComplianceStore, reset_compliance_store
from credit_engine.services.risk import evaluate_proposal


@pytest.fixture(autouse=True)
def _reset_rag_singleton() -> None:
    reset_compliance_store()
    yield
    reset_compliance_store()


def test_chunk_markdown_sections_splits_on_h2() -> None:
    md = "# Title\n\nintro\n\n## Alpha\n\nbody a\n\n## Beta\n\nbody b\n"
    chunks = chunk_markdown_sections(md)
    assert len(chunks) == 3
    assert chunks[1].title == "Alpha"
    assert "body a" in chunks[1].text


def test_load_default_policy_chunks() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "credit_engine"
        / "rag"
        / "policies"
        / "credit_policy_pt.md"
    )
    chunks = load_policy_chunks(path)
    assert len(chunks) >= 4
    assert any("score" in c.text.lower() for c in chunks)


def test_split_and_window_chunks_keep_parent() -> None:
    sections = chunk_markdown_sections(
        "## Alpha\n\nFirst sentence. Second sentence. Third sentence.\n"
    )
    windows = window_chunks(sections, window_sentences=2, overlap=0)
    assert len(windows) >= 2
    assert all(window.parent_id == sections[0].chunk_id for window in windows)
    assert "First sentence" in windows[0].text


def test_split_into_sentences_handles_bullets() -> None:
    text = "Intro line.\n- Bullet one\n- Bullet two"
    parts = split_into_sentences(text)
    assert len(parts) >= 2


def test_hashing_embedding_is_deterministic() -> None:
    fn = HashingEmbeddingFunction(dimensions=64)
    a = fn(["limite emergencial biro"])
    b = fn(["limite emergencial biro"])
    assert [list(vec) for vec in a] == [list(vec) for vec in b]
    assert len(list(a[0])) == 64


def test_rrf_prefers_docs_strong_in_both_lists() -> None:
    fused = reciprocal_rank_fusion(
        [
            ["a", "b", "c"],
            ["b", "c", "a"],
        ],
        k=60,
    )
    assert fused[0] == "b"
    assert set(fused) == {"a", "b", "c"}


def test_lexical_rank_orders_by_overlap() -> None:
    ranked = rank_ids_by_lexical(
        "limite emergencial birô",
        ids=["x", "y"],
        documents=[
            "faixas de score e renda",
            "limite emergencial birô indisponível",
        ],
    )
    assert ranked[0] == "y"
    assert lexical_overlap_score("limite", "limite emergencial") > 0


def test_compliance_store_retrieves_score_policy() -> None:
    store = ComplianceStore(ephemeral=True)
    store.ensure_indexed()
    hits = store.query("score abaixo de 300 negação limite zero", top_k=2)
    assert hits
    assert any("300" in hit for hit in hits)


def test_compliance_store_expands_window_to_parent_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "credit_engine.rag.store.settings.SENTENCE_WINDOW",
        True,
    )
    monkeypatch.setattr(
        "credit_engine.rag.store.settings.RRF_ENABLED",
        True,
    )
    store = ComplianceStore(ephemeral=True)
    store.ensure_indexed()
    hits = store.query("contingência birô limite emergencial R$ 500", top_k=1)
    assert hits
    # Parent section should include surrounding contingency context.
    assert "500" in hits[0] or "emergencial" in hits[0].lower()
    assert "##" in hits[0] or "Contingência" in hits[0] or "birô" in hits[0].lower()


def test_build_retrieval_query_emergency() -> None:
    q = build_retrieval_query(
        score=900,
        band=RiskBand.PREMIUM,
        status=ProposalStatus.APPROVED,
        emergency=True,
    )
    assert "emergencial" in q


class FixedScoreBureau:
    def __init__(self, score: int) -> None:
        self._score = score

    async def fetch_credit_score(self, cpf: str) -> int:
        _ = cpf
        return self._score


async def test_evaluate_proposal_attaches_compliance_excerpts() -> None:
    store = ComplianceStore(ephemeral=True)
    store.ensure_indexed()
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Maria Silva",
            cpf="12345678901",
            monthly_income="10000.00",
            credit_score=650,
        ),
        bureau=FixedScoreBureau(650),
        compliance_store=store,
    )
    assert decision.status is ProposalStatus.APPROVED
    assert decision.compliance_excerpts
    assert "Compliance:" in decision.reason


async def test_evaluate_emergency_retrieves_contingency_policy() -> None:
    store = ComplianceStore(ephemeral=True)
    store.ensure_indexed()
    decision = await evaluate_proposal(
        ProposalCreate(
            applicant_name="Ana",
            cpf="12345678901",
            monthly_income="20000.00",
            credit_score=800,
        ),
        bureau=UnavailableBureauClient(),
        compliance_store=store,
    )
    assert decision.compliance_excerpts
    joined = " ".join(decision.compliance_excerpts).lower()
    assert "500" in joined or "emergencial" in joined or "birô" in joined


def test_retrieve_skips_when_rag_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "credit_engine.rag.retrieve.settings.ENABLED",
        False,
    )
    excerpts = retrieve_compliance_excerpts(
        score=650,
        band=RiskBand.STANDARD,
        status=ProposalStatus.APPROVED,
    )
    assert excerpts == []
