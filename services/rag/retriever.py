import chromadb
from chromadb.api.models.Collection import Collection

from core.config import ChromaSettings
from schemas.proposal import ComplianceRuleHit, CreditProposal
from services.rag.rrf import reciprocal_rank_fusion


class ComplianceRetriever:
    def __init__(self, settings: ChromaSettings) -> None:
        self._settings = settings
        self._client = chromadb.PersistentClient(path=str(settings.persist_dir))

    @property
    def collection(self) -> Collection:
        return self._client.get_collection(name=self._settings.collection_name)

    def retrieve_for_proposal(self, proposal: CreditProposal) -> list[ComplianceRuleHit]:
        query = self._build_query(proposal)
        return self.retrieve(query)

    def retrieve(self, query: str) -> list[ComplianceRuleHit]:
        sentence_results = self.collection.query(
            query_texts=[query],
            n_results=self._settings.top_k,
            where={"chunk_type": "sentence_window"},
        )
        paragraph_results = self.collection.query(
            query_texts=[query],
            n_results=self._settings.top_k,
            where={"chunk_type": "paragraph"},
        )

        sentence_ids = sentence_results["ids"][0] if sentence_results["ids"] else []
        paragraph_ids = paragraph_results["ids"][0] if paragraph_results["ids"] else []

        fused = reciprocal_rank_fusion(
            [sentence_ids, paragraph_ids],
            k=self._settings.rrf_k,
            top_k=self._settings.top_k,
        )

        documents_by_id = self._map_documents(sentence_results, paragraph_results)
        metadata_by_id = self._map_metadata(sentence_results, paragraph_results)

        hits: list[ComplianceRuleHit] = []
        seen_texts: set[str] = set()
        for doc_id, score in fused:
            rule_text = documents_by_id[doc_id]
            if rule_text in seen_texts:
                continue
            seen_texts.add(rule_text)
            hits.append(
                ComplianceRuleHit(
                    rule_text=rule_text,
                    relevance_score=round(score, 6),
                    chunk_type=metadata_by_id[doc_id]["chunk_type"],
                    source=metadata_by_id[doc_id].get("source", "compliance_manual"),
                )
            )
        return hits

    @staticmethod
    def _build_query(proposal: CreditProposal) -> str:
        score_part = (
            f"score {proposal.credit_score}"
            if proposal.credit_score is not None
            else "score não informado"
        )
        return (
            f"Regras de crédito para região {proposal.region}, {score_part}, "
            f"renda mensal R$ {proposal.monthly_income:.2f}, "
            f"conta {proposal.account_type}."
        )

    @staticmethod
    def _map_documents(sentence_results: dict, paragraph_results: dict) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for result_set in (sentence_results, paragraph_results):
            ids = result_set.get("ids", [[]])[0]
            documents = result_set.get("documents", [[]])[0]
            for doc_id, document in zip(ids, documents, strict=True):
                mapping[doc_id] = document
        return mapping

    @staticmethod
    def _map_metadata(sentence_results: dict, paragraph_results: dict) -> dict[str, dict]:
        mapping: dict[str, dict] = {}
        for result_set in (sentence_results, paragraph_results):
            ids = result_set.get("ids", [[]])[0]
            metadatas = result_set.get("metadatas", [[]])[0]
            for doc_id, metadata in zip(ids, metadatas, strict=True):
                mapping[doc_id] = metadata
        return mapping
