import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RUNS_PATH = DATA_DIR / "runs.json"
PRODUCTS_PATH = DATA_DIR / "products.json"


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RUNS_PATH.exists():
        RUNS_PATH.write_text("[]", encoding="utf-8")
    if not PRODUCTS_PATH.exists():
        PRODUCTS_PATH.write_text("[]", encoding="utf-8")


def _load_runs() -> List[Dict[str, object]]:
    _ensure_storage()
    try:
        return json.loads(RUNS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _load_products() -> List[Dict[str, object]]:
    _ensure_storage()
    try:
        return json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_runs(runs: List[Dict[str, object]]) -> None:
    _ensure_storage()
    RUNS_PATH.write_text(json.dumps(runs, indent=2), encoding="utf-8")


def _save_products(products: List[Dict[str, object]]) -> None:
    _ensure_storage()
    PRODUCTS_PATH.write_text(json.dumps(products, indent=2), encoding="utf-8")


def add_product(name: str) -> Dict[str, object]:
    products = _load_products()
    product_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "product_id": product_id,
        "name": name,
        "created_at": timestamp,
        "subreddits": [],
    }
    products.insert(0, record)
    _save_products(products)
    return record


def list_products() -> List[Dict[str, object]]:
    return _load_products()


def find_product_by_name(name: str) -> Optional[Dict[str, object]]:
    products = _load_products()
    for product in products:
        if product.get("name", "").lower() == name.lower():
            return product
    return None


def get_product(product_id: str) -> Optional[Dict[str, object]]:
    products = _load_products()
    for product in products:
        if product.get("product_id") == product_id:
            return product
    return None


def update_product(product_id: str, updates: Dict[str, object]) -> Optional[Dict[str, object]]:
    products = _load_products()
    for idx, product in enumerate(products):
        if product.get("product_id") == product_id:
            updated = {**product, **updates}
            products[idx] = updated
            _save_products(products)
            return updated
    return None


def add_run(product_id: str, result: Dict[str, object]) -> Dict[str, object]:
    runs = _load_runs()
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "run_id": run_id,
        "created_at": timestamp,
        "product_id": product_id,
        **result,
    }
    runs.insert(0, record)
    _save_runs(runs)
    return record


def list_runs(product_id: Optional[str] = None) -> List[Dict[str, object]]:
    runs = _load_runs()
    if product_id:
        runs = [run for run in runs if run.get("product_id") == product_id]
    return runs


def get_run(run_id: str) -> Optional[Dict[str, object]]:
    runs = _load_runs()
    for run in runs:
        if run.get("run_id") == run_id:
            return run
    return None


def get_latest_run(product_id: str) -> Optional[Dict[str, object]]:
    runs = _load_runs()
    for run in runs:
        if run.get("product_id") == product_id:
            return run
    return None


def update_run(run_id: str, updates: Dict[str, object]) -> Optional[Dict[str, object]]:
    runs = _load_runs()
    for idx, run in enumerate(runs):
        if run.get("run_id") == run_id:
            updated = {**run, **updates}
            runs[idx] = updated
            _save_runs(runs)
            return updated
    return None
