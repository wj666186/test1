"""入口：python run.py [mock|real]"""

import sys

from eval.pipeline import run

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
    run(mode=mode)
