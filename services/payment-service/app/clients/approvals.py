from typing import Protocol
from uuid import uuid4


class ApprovalClient(Protocol):
    def create_workflow(self, document_id: str, document_type: str) -> str: ...


class FakeApprovalClient:
    def create_workflow(self, document_id: str, document_type: str) -> str:
        return f"approval-{uuid4()}"
