from pathlib import Path

from api.learning_gate import build_backend_env, build_foundation_command


def test_build_backend_env_for_transformers(tmp_path: Path) -> None:
    env = build_backend_env(
        model_backend="transformers-causal-lm",
        base_model="gpt2",
        backend_output_dir=tmp_path / "model",
        backend_device="cpu",
        backend_max_steps=3,
        backend_lr=0.0001,
    )
    assert env["AILOVANTA_MODEL_BACKEND"] == "transformers-causal-lm"
    assert env["AILOVANTA_BASE_MODEL"] == "gpt2"
    assert env["AILOVANTA_BACKEND_OUTPUT_DIR"] == str(tmp_path / "model")
    assert env["AILOVANTA_BACKEND_DEVICE"] == "cpu"
    assert env["AILOVANTA_BACKEND_MAX_STEPS"] == "3"
    assert env["AILOVANTA_BACKEND_LR"] == "0.0001"


def test_foundation_command_still_uses_checkpoint_flags(tmp_path: Path) -> None:
    command = build_foundation_command(
        tmp_path,
        tmp_path / "job.json",
        tmp_path / "result.json",
        execute_checkpoints=True,
        checkpoint_output_root=tmp_path / "ckpts",
    )
    assert "--execute-checkpoints" in command
    assert "--checkpoint-output-root" in command
