from __future__ import annotations

from pathlib import Path

root = Path(__file__).resolve().parent


def read(rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    assert condition, message


required_files = [
    "README.md",
    "VERSION",
    "index.html",
    "api/main.py",
    "api/conversation_store.py",
    "api/runtime_router.py",
    "api/runtime_store.py",
    "api/rights_proof_registry.py",
    "api/code_training_jobs.py",
    "scripts/export_code_training_job.py",
    "docs/AUTH_MODEL.md",
    "docs/NEXT_STAGE_PRD.md",
    "docs/CHATGPT_STYLE_UI.md",
    "docs/AILOVANTA_CODE_DISTRIBUTED_PLAN.md",
    "docs/AUTOTRAIN_ARCHITECTURE.md",
    "docs/RIGHTS_PROOF_REGISTRY.md",
    "docs/GITHUB_CODE_TRAINING.md",
    "docs/CODE_DISTILLATION.md",
    "tests/test_guest_chat_flow.py",
    "tests/test_rights_proof_registry.py",
    "tests/test_code_training_job_export.py",
    ".github/workflows/validate.yml",
]

for rel in required_files:
    require((root / rel).exists(), f"missing file: {rel}")

require(read("VERSION").strip() == "1.11.0", "unexpected version")

checks = {
    "index.html": ["data-app", "data-guest-mode", "/ailovanta/v1/chat", "conversationList"],
    "api/main.py": ["/ailovanta/v1/chat", "/ailovanta/v1/run", "context_messages_used"],
    "api/rights_proof_registry.py": ["RightsProofRegistry", "agreement_id", "commercial_use_allowed", "distillation_allowed", "can_train"],
    "api/code_training_jobs.py": ["distributed_required", "code_lora", "code_qlora", "code_distill", "code_eval"],
    "scripts/export_code_training_job.py": ["ailovanta.training_job.v1", "distributed_required", "--rights-id"],
    "docs/AILOVANTA_CODE_DISTRIBUTED_PLAN.md": ["Ailovanta-Code", "distributed_required", "Runtime Router"],
    "docs/AUTOTRAIN_ARCHITECTURE.md": ["AutoTrain", "distributed_required", "Validator nodes", "Aggregator"],
    "docs/RIGHTS_PROOF_REGISTRY.md": ["Rights Proof Registry", "commercial_use_allowed", "distillation_allowed"],
    "docs/GITHUB_CODE_TRAINING.md": ["GitHub Repo Understanding", "rights_id", "pull request"],
    "docs/CODE_DISTILLATION.md": ["Code Distillation", "test_pass_rate", "distributed training"],
    "tests/test_rights_proof_registry.py": ["test_active_rights_can_train", "test_inactive_rights_cannot_train"],
    "tests/test_code_training_job_export.py": ["test_code_lora_job_is_distributed", "test_inactive_rights_cannot_create_job"],
}

for rel, markers in checks.items():
    text = read(rel)
    for marker in markers:
        require(marker in text, f"missing marker {marker} in {rel}")

print("Ailovanta validation passed.")
