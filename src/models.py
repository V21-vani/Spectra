from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class TestResult:
    test_file: str
    test_name: str
    status: str  # PASSED | FAILED | SKIPPED | ERROR
    duration: float  # milliseconds
    coverage: float  # 0-100
    error_message: Optional[str] = None
    id: str = field(default_factory=lambda: str(time.time_ns()))


@dataclass
class TestSession:
    name: str
    timestamp: float
    results: list
