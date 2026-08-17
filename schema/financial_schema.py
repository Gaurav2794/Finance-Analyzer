"""
Financial Data Schema Contract (Team 1 Frozen Output Contract)
Validated before handing over to Segment 2 (Review Engine) and LLM Model.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CompanyMetadata(BaseModel):
    name: str
    cin_or_ticker: Optional[str] = "N/A"
    industry: Optional[str] = "General Industry"
    reporting_standard: Optional[str] = "Ind AS / IFRS"
    statement_type: Optional[str] = "Consolidated"
    currency: str = "INR"
    scale: str = "Crores"
    multiplier: float = 10000000.0


class PeriodInfo(BaseModel):
    period_key: str
    label: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_audited: bool = True


class DocumentMetadata(BaseModel):
    document_id: str
    source_file: str
    extraction_timestamp: str
    parser_version: str = "1.0.0"
    company: CompanyMetadata
    periods: List[PeriodInfo]


class SourceTrace(BaseModel):
    file: str
    page: Optional[int] = None
    table_index: Optional[int] = None
    note_ref: Optional[str] = None
    raw_label: Optional[str] = None
    bbox: Optional[List[float]] = None


class ExtractedNote(BaseModel):
    note_number: str
    topic: str
    text: str
    disclosed_value: Optional[float] = None
    related_party_count: Optional[int] = None
    transaction_count: Optional[int] = None
    source: Optional[SourceTrace] = None


class DocumentQualityMetrics(BaseModel):
    file_validity: str
    page_count: int
    ocr_quality: float
    extraction_completeness: str
    extraction_completeness_pct: float
    missing_sections: List[str] = Field(default_factory=list)
    missing_values: int = 0
    currency: str
    unit: str
    period: List[str]
    data_quality_status: str


class ExtractionItemMetrics(BaseModel):
    count: int
    extracted_keys: Optional[List[str]] = Field(default_factory=list)
    topics: Optional[List[str]] = Field(default_factory=list)


class ExtractionMetrics(BaseModel):
    balance_sheet_values: ExtractionItemMetrics
    income_statement_values: ExtractionItemMetrics
    cash_flow_values: ExtractionItemMetrics
    disclosure_values: ExtractionItemMetrics


class RAGMetrics(BaseModel):
    chunk_count: int
    retrieval_relevance: float
    top_k_results: int = 5
    source_page_accuracy: str
    source_page_accuracy_pct: float
    retrieval_latency: str
    retrieval_latency_ms: int


class Team1Metrics(BaseModel):
    document_quality: DocumentQualityMetrics
    extraction: ExtractionMetrics
    rag: RAGMetrics


class FinancialDataContract(BaseModel):
    metadata: DocumentMetadata
    team1_metrics: Team1Metrics
    balance_sheet: Dict[str, Any]
    income_statement: Dict[str, Any]
    cash_flow_statement: Dict[str, Any]
    extracted_notes_and_disclosures: Optional[List[ExtractedNote]] = Field(default_factory=list)
