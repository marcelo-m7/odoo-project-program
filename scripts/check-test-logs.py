import re
import sys
from pathlib import Path

for filename in sys.argv[1:]:
    text = Path(filename).read_text()
    summaries = re.findall(r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", text)
    if not summaries:
        raise SystemExit(f"No Odoo test summary in {filename}")
    if any(int(f) or int(e) or int(n) == 0 for f, e, n in summaries):
        raise SystemExit(f"Odoo tests failed in {filename}: {summaries}")
    if "Modules loaded." not in text:
        raise SystemExit(f"Module loading incomplete: {filename}")
    print(filename, summaries)
