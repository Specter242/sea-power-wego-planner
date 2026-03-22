#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from planner.server import create_server


def main():
    parser = argparse.ArgumentParser(description="Run the Sea Power WEGO PvP planner.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parent / "data" / "planner.sqlite3"),
        help="SQLite database path.",
    )
    args = parser.parse_args()

    server = create_server(args.host, args.port, args.db)
    print(f"Sea Power planner running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
