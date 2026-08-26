from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class ApprovalRevisionRequest:
    id: str
    document_id: str
    reason_code: str
    detail: str
    requested_by: str
    status: str


class ApprovalClient(Protocol):
    def create_workflow(self, document_id: str, document_type: str) -> str: ...

    def get_revision_request(
        self,
        revision_request_id: str,
        document_id: str,
    ) -> ApprovalRevisionRequest: ...


class FakeApprovalClient:
    def create_workflow(self, document_id: str, document_type: str) -> str:
        return f"approval-{uuid4()}"

    def get_revision_request(
        self,
        revision_request_id: str,
        document_id: str,
    ) -> ApprovalRevisionRequest:
        if revision_request_id == "missing-revision":
            raise LookupError("Approval revision request was not found")
        status = "CLOSED" if revision_request_id == "closed-revision" else "OPEN"
        return ApprovalRevisionRequest(
            id=revision_request_id,
            document_id=document_id,
            reason_code="PAYMENT_INFORMATION_INCORRECT",
            detail="Check billed quantity against reconciliation records",
            requested_by="mock-reviewer",
            status=status,
        )
