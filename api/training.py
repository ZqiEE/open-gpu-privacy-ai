from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal
from uuid import uuid4


TrainingKind = Literal["rag_import", "lora_micro", "evaluation_batch", "robot_memory_tune"]


@dataclass
class TrainingJobSpec:
    kind: str
    name: str
    dataset_uri: str
    base_model: str
    max_steps: int = 100
    notes: str = ""

    def to_scheduler_job(self) -> dict:
        return {
            "job_id": "train_" + uuid4().hex[:12],
            "job_type": self.kind,
            "payload": asdict(self),
        }


@dataclass
class ModelVersionSpec:
    name: str
    base_model: str
    source_job_id: str
    notes: str = ""

    def to_record(self) -> dict:
        return {
            "model_id": "model_" + uuid4().hex[:12],
            "name": self.name,
            "base_model": self.base_model,
            "source_job_id": self.source_job_id,
            "notes": self.notes,
        }


class TrainingPlanner:
    def build_job(self, kind: TrainingKind, name: str, dataset_uri: str, base_model: str, max_steps: int, notes: str) -> dict:
        spec = TrainingJobSpec(kind=kind, name=name, dataset_uri=dataset_uri, base_model=base_model, max_steps=max_steps, notes=notes)
        return spec.to_scheduler_job()

    def build_model_version(self, name: str, base_model: str, source_job_id: str, notes: str) -> dict:
        return ModelVersionSpec(name=name, base_model=base_model, source_job_id=source_job_id, notes=notes).to_record()
