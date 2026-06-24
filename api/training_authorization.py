from __future__ import annotations

from api.data_rights_store import DataRightsStore


TRAINING_USE_BY_JOB_TYPE = {
    "rag_import": "rag",
    "lora_micro": "finetune",
    "evaluation_batch": "eval",
    "private_memory_tune": "finetune",
}


def authorize_training_source(store: DataRightsStore, job_type: str, source_id: str | None) -> dict:
    if not source_id:
        return {"authorized": True, "source": None, "reason": "no data source attached"}
    requested_use = TRAINING_USE_BY_JOB_TYPE.get(job_type, "finetune")
    return store.check_use(source_id, requested_use)
