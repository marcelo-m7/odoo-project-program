import re
import sys
from pathlib import Path

for filename in sys.argv[1:]:
    log = Path(filename).read_text()
    summaries = re.findall(r'(\d+) failed, (\d+) error\(s\) of (\d+) tests', log)
    assert summaries, f'No test summary: {filename}'
    assert all(int(f) == 0 and int(e) == 0 and int(n) > 0 for f, e, n in summaries), summaries
    assert 'Modules loaded.' in log, f'Module loading incomplete: {filename}'
    print(filename, summaries)
