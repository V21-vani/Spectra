import subprocess
import sys
import tempfile
import os
import json
from typing import Callable, Optional
from .parser import parse_junit_xml
from .models import TestResult


def run_pytest(
    path: str,
    on_line: Optional[Callable[[str], None]] = None,
    coverage: bool = False,
) -> tuple[list[TestResult], str, str]:
    """Run pytest on *path*, stream output via on_line, return (results, stdout, error)."""
    xml_fd, xml_path = tempfile.mkstemp(suffix=".xml")
    os.close(xml_fd)

    cov_path: Optional[str] = None
    if coverage:
        cov_fd, cov_path = tempfile.mkstemp(suffix=".json")
        os.close(cov_fd)

    try:
        cmd = [
            sys.executable, "-m", "pytest", path,
            f"--junit-xml={xml_path}", "-v", "--tb=short",
        ]
        if coverage and cov_path:
            cmd += [
                f"--cov={path}",
                f"--cov-report=json:{cov_path}",
                "--cov-report=",  # suppress extra terminal table
            ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        lines = []
        for line in proc.stdout:
            lines.append(line)
            if on_line:
                on_line(line)

        proc.wait()
        stdout = "".join(lines)

        if os.path.exists(xml_path) and os.path.getsize(xml_path) > 0:
            results, err = parse_junit_xml(xml_path)
        else:
            results, err = [], "pytest produced no XML output — is pytest installed in that environment?"

        if coverage and cov_path and os.path.exists(cov_path) and os.path.getsize(cov_path) > 0:
            _apply_coverage(results, cov_path)

        return results, stdout, err

    except FileNotFoundError:
        return [], "", "Python / pytest not found. Make sure pytest is installed."
    except Exception as exc:
        return [], "", str(exc)
    finally:
        if os.path.exists(xml_path):
            os.unlink(xml_path)
        if cov_path and os.path.exists(cov_path):
            os.unlink(cov_path)


def _apply_coverage(results: list[TestResult], cov_json_path: str) -> None:
    """Read coverage.json and assign per-file coverage % to each TestResult."""
    try:
        with open(cov_json_path, encoding="utf-8") as f:
            data = json.load(f)

        # basename (no ext, lowercased) -> coverage %
        file_cov: dict[str, float] = {}
        for fpath, fdata in data.get("files", {}).items():
            pct = fdata.get("summary", {}).get("percent_covered", 0.0)
            stem = os.path.normcase(os.path.splitext(os.path.basename(fpath))[0])
            file_cov[stem] = round(pct, 1)

        for r in results:
            # JUnit classname is like "tests.test_auth" or "test_auth"
            test_stem = os.path.normcase(r.test_file.split(".")[-1])

            # Prefer the source file (strip test_ / _test prefix/suffix)
            source_stem = test_stem
            if source_stem.startswith("test_"):
                source_stem = source_stem[5:]
            elif source_stem.endswith("_test"):
                source_stem = source_stem[:-5]

            if source_stem and source_stem != test_stem and source_stem in file_cov:
                r.coverage = file_cov[source_stem]
            elif test_stem in file_cov:
                r.coverage = file_cov[test_stem]
    except Exception:
        pass  # coverage parse failure is non-fatal
