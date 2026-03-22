#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from planner.server import create_server


def main():
    parser = argparse.ArgumentParser(description="Run the Sea Power local campaign planner.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--campaign",
        default=str(Path(__file__).resolve().parent / "data" / "current_campaign.json"),
        help="Local JSON campaign path.",
    )
    parser.add_argument(
        "--legacy-db",
        default=str(Path(__file__).resolve().parent / "data" / "planner.sqlite3"),
        help="Optional legacy SQLite database path used for one-time migration.",
    )
    args = parser.parse_args()

    server = create_server(args.host, args.port, args.campaign, legacy_db_path=args.legacy_db)
    print(f"Sea Power planner running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
