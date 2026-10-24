"""Entry point for image2travel-mcp."""
import sys


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'seed':
            from .ingestion.cli import main as ingest_main
            sys.argv = [sys.argv[0]] + sys.argv[1:]
            ingest_main()
            return
        elif cmd == 'data-check':
            from .ingestion.cli import main as ingest_main
            sys.argv = [sys.argv[0]] + sys.argv[1:]
            ingest_main()
            return
    from .server import main as server_main
    server_main()


if __name__ == "__main__":
    sys.exit(main())
