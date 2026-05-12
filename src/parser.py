import xml.etree.ElementTree as ET
from .models import TestResult


def parse_junit_xml(path: str) -> tuple[list[TestResult], str]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()

        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        elif root.tag == "testsuite":
            suites = [root]
        else:
            return [], f"Unrecognised root tag: {root.tag}"

        results = []
        for suite in suites:
            suite_name = suite.get("name", "unknown")
            for tc in suite.findall("testcase"):
                name = tc.get("name", "unknown")
                classname = tc.get("classname", suite_name)
                duration = float(tc.get("time", 0)) * 1000  # s → ms

                failure = tc.find("failure")
                error = tc.find("error")
                skipped = tc.find("skipped")

                if failure is not None:
                    status = "FAILED"
                    msg = failure.get("message", "") or (failure.text or "")
                elif error is not None:
                    status = "ERROR"
                    msg = error.get("message", "") or (error.text or "")
                elif skipped is not None:
                    status = "SKIPPED"
                    msg = skipped.get("message", "")
                else:
                    status = "PASSED"
                    msg = ""

                results.append(TestResult(
                    test_file=classname,
                    test_name=name,
                    status=status,
                    duration=round(duration, 2),
                    coverage=0.0,
                    error_message=msg[:300] if msg else None,
                ))

        return results, ""
    except Exception as exc:
        return [], str(exc)
