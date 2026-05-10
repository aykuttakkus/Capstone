from __future__ import annotations

import os

from server.run import main


if __name__ == "__main__":
    main(
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=os.getenv("BACKEND_PORT", "8000"),
    )
