#!/usr/bin/env bash
# Run a command. CPython 3.11 on the current GitHub runner sometimes SIGSEGVs
# in native shutdown after the program has already finished. Exit 139 is
# accepted only when the completion check below succeeds. Any earlier crash,
# or a real failure, still fails the job.
set -u
marker="$1"
shift
log="$(mktemp)"
set +e
"$@" 2>&1 | tee "$log"
ec=${PIPESTATUS[0]}
set -e
if [ "$ec" -eq 0 ]; then
  rm -f "$log"
  exit 0
fi
if [ "$ec" -ne 139 ]; then
  rm -f "$log"
  exit "$ec"
fi
if [ "$marker" = "__junit__" ] && [ -f pytest-report.xml ]; then
  python - << 'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse("pytest-report.xml").getroot()
suites = [root] if root.tag == "testsuite" else list(root)
failures = errors = tests = 0
for suite in suites:
    failures += int(suite.attrib.get("failures", 0))
    errors += int(suite.attrib.get("errors", 0))
    tests += int(suite.attrib.get("tests", 0))
print(f"pytest process exited 139; junit tests={tests} failures={failures} errors={errors}")
sys.exit(0 if tests > 0 and failures == 0 and errors == 0 else 1)
PY
  status=$?
  rm -f "$log"
  exit "$status"
fi
if grep -qF "$marker" "$log"; then
  echo "process exited 139 after printing: $marker"
  rm -f "$log"
  exit 0
fi
echo "process exited 139 before printing: $marker"
rm -f "$log"
exit 139
