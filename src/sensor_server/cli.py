"""Command-line interface for the sensor server."""

import argparse
import sys


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sensor-server",
        description="Numpy Data Server - FastAPI backend for numpy data transfer",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Start the server")
    run_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    run_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Version command
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "run":
        return run_server(args.host, args.port, args.reload)
    elif args.command == "version":
        from sensor_server import __version__
        print(f"sensor-server {__version__}")
        return 0
    else:
        parser.print_help()
        return 1


def run_server(host: str, port: int, reload: bool) -> int:
    """Start the uvicorn server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required. Install with: pip install uvicorn[standard]")
        return 1

    uvicorn.run(
        "sensor_server.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
