#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    from main import run_once
    from src.utils.config import config
    import uvicorn
    from api.main import app

    run_once(config.DEFAULT_CITY, config.PLATFORMS)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
