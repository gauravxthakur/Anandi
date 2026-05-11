"""Path configuration for the fetal biometry project."""

from __future__ import annotations

from pathlib import Path


def _is_project_root(p: Path) -> bool:
    return (
        (p / "requirements.txt").exists()
        and (p / "data").exists()
        and (p / "models").exists()
    )


def find_project_root(start: Path | None = None) -> Path:
    """Find the project root directory by looking for marker files."""
    if start is None:
        start = Path(__file__).resolve()

    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent

    for candidate in [cur, *cur.parents]:
        if _is_project_root(candidate):
            return candidate

    raise RuntimeError(
        "Could not detect project root. Expected to find requirements.txt, data/, models/ in some parent directory."
    )


PROJECT_ROOT = find_project_root()


class Paths:
    ROOT = str(PROJECT_ROOT)

    DATA_DIR = str(PROJECT_ROOT / "data")
    MODELS_DIR = str(PROJECT_ROOT / "models")
    RESULTS_DIR = str(PROJECT_ROOT / "results")

    VALIDATION_DIR = str(PROJECT_ROOT / "data" / "validation")
    VALIDATION_IMAGES_DIR = str(PROJECT_ROOT / "data" / "validation" / "images")
    VALIDATION_LABELS_DIR = str(PROJECT_ROOT / "data" / "validation" / "labels")
    VALIDATION_CSV = str(PROJECT_ROOT / "data" / "validation" / "val_set_pixel_size_and_HC.csv")

    MODEL_TEST = str(PROJECT_ROOT / "models" / "test_model.pth")

    PREDICTIONS_DIR = str(PROJECT_ROOT / "results" / "predictions")
    PREDICTIONS_EDGE_DIR = str(PROJECT_ROOT / "results" / "predictions_edge")
    VISUALIZATIONS_DIR = str(PROJECT_ROOT / "results" / "visualizations")

    ELLIP_PARAMS_CSV = str(PROJECT_ROOT / "results" / "ellip_params.csv")
    EVAL_RESULTS_CSV = str(PROJECT_ROOT / "results" / "eval_results.csv")


def ensure_results_dirs() -> None:
    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results" / "predictions").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results" / "predictions_edge").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results" / "visualizations").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(f"PROJECT_ROOT={PROJECT_ROOT}")
    print(f"VALIDATION_IMAGES_DIR={Paths.VALIDATION_IMAGES_DIR}")
    print(f"MODEL_TEST exists={(PROJECT_ROOT / 'models' / 'test_model.pth').exists()}")
