from pathlib import Path
import runpy


ROOT_MAIN = Path(__file__).resolve().parents[1] / "main.py"

runpy.run_path(str(ROOT_MAIN), run_name="__main__")
