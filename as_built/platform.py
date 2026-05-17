"""
Platform — the read/write surface the worker operates on.

Wraps a dbt project backed by DuckDB. The worker uses this to inspect
models, apply changes, trigger builds, and read the dashboard output.
Five methods; one obvious way to do each thing.
"""

import csv
import subprocess
import sys
from pathlib import Path
from typing import Any

# dbt binary lives alongside this Python interpreter (inside the venv).
_DBT = Path(sys.executable).parent / "dbt"


class Platform:
    def __init__(self, root: Path | None = None) -> None:
        if root is None:
            root = Path(__file__).parent.parent / "platform"
        self.root = root
        self._models_dir = root / "models"
        self._db_path = root / "warehouse.duckdb"
        self._dashboard_path = root / "dashboard.csv"

    # ---- read surface -------------------------------------------------------

    def list_models(self) -> list[str]:
        """Stem names of all .sql files under models/, sorted."""
        return sorted(p.stem for p in self._models_dir.rglob("*.sql"))

    def read_model(self, name: str) -> str:
        """SQL source for the named model. Raises FileNotFoundError if absent."""
        matches = list(self._models_dir.rglob(f"{name}.sql"))
        if not matches:
            raise FileNotFoundError(f"No model named {name!r}")
        return matches[0].read_text()

    def read_dashboard(self) -> list[dict[str, Any]]:
        """Dashboard rows as a list of dicts. Requires a prior build()."""
        if not self._dashboard_path.exists():
            raise FileNotFoundError("dashboard.csv not found — run build() first")
        with open(self._dashboard_path, newline="") as f:
            return list(csv.DictReader(f))

    # ---- write surface ------------------------------------------------------

    def write_model(self, name: str, sql: str) -> None:
        """Overwrite the SQL of an existing model. Raises FileNotFoundError if absent."""
        matches = list(self._models_dir.rglob(f"{name}.sql"))
        if not matches:
            raise FileNotFoundError(f"No model named {name!r}")
        matches[0].write_text(sql)

    # ---- build --------------------------------------------------------------

    def build(self) -> subprocess.CompletedProcess[str]:
        """Run dbt build against the DuckDB warehouse.

        On success, exports mart_revenue_summary to dashboard.csv and returns
        the completed process. On failure, returns the process with a non-zero
        returncode (stdout/stderr are captured for the caller to inspect).
        """
        # Run from the repo root so dbt's relative seed paths resolve correctly.
        # dbt stores root_path as the value passed to --project-dir; if that's
        # a relative string like "platform", DuckDB resolves seed CSVs against
        # the process cwd — which must therefore be the repo root.
        result = subprocess.run(
            [
                str(_DBT), "build",
                "--project-dir", str(self.root),
                "--profiles-dir", str(self.root),
            ],
            cwd=self.root.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            self._export_dashboard()
        return result

    # ---- internal -----------------------------------------------------------

    def _export_dashboard(self) -> None:
        """Write mart_revenue_summary to dashboard.csv via DuckDB COPY."""
        import duckdb  # imported late; only needed after a successful build

        con = duckdb.connect(str(self._db_path))
        try:
            con.execute(
                f"COPY (SELECT * FROM main.mart_revenue_summary ORDER BY total_revenue_eur DESC) "
                f"TO '{self._dashboard_path}' (HEADER, DELIMITER ',')"
            )
        finally:
            con.close()
