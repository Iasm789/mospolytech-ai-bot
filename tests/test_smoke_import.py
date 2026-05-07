import importlib.util
import os
import sys
from pathlib import Path


def test_main_import_smoke():
    os.environ.setdefault("BOT_TOKEN", "123456:abcdefghijklmnopqrstuvwxyz123456")
    main_path = Path(__file__).resolve().parents[1] / "main.py"
    project_root = str(main_path.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    spec = importlib.util.spec_from_file_location("main", main_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
