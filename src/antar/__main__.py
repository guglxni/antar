"""antar CLI.

  python -m antar run <repo> [--mode report|issues|pr] [--allow-pr] [--max-prs N] [--offline]
  python -m antar mcp                 # serve the MCP tools
"""
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv
from rich import print as rprint

from . import orchestrator


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="antar", description="Find the code↔literature gap.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run the pipeline against a repo")
    run_p.add_argument("repo", help="local path or owner/name")
    run_p.add_argument("--mode", choices=["report", "issues", "pr"], default="report")
    run_p.add_argument("--allow-pr", action="store_true", help="permit opening PRs")
    run_p.add_argument("--max-prs", type=int, default=1)
    run_p.add_argument("--offline", action="store_true", help="replay cached run (no API)")

    sub.add_parser("mcp", help="serve antar as an MCP server")

    args = parser.parse_args(argv)

    if args.cmd == "mcp":
        from .mcp_server import mcp
        mcp.run()
        return 0

    if args.cmd == "run":
        if args.offline:
            rprint("[yellow]Offline replay not yet wired — use a cached golden run.[/yellow]")
            return 0
        rprint(f"[cyan]antar[/cyan] → repo={args.repo} mode={args.mode}")
        rep = orchestrator.run(args.repo, mode=args.mode, allow_pr=args.allow_pr,
                               max_prs=args.max_prs, offline=args.offline)
        rprint("\n[bold green]Done[/bold green]")
        rprint(f"  techniques: {rep.techniques}")
        rprint(f"  papers:     {rep.papers}")
        rprint(f"  verified gaps: {rep.verified_gaps}")
        if rep.issues:
            rprint(f"  issues: {rep.issues}")
        if rep.prs:
            rprint(f"  prs: {rep.prs}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
