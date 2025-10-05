#!/usr/bin/env python3
"""CLI for reapplying structured pre-filter logic to persisted job reviews."""

import argparse
import asyncio
from typing import List

from loguru import logger

from app.core.config import configure_logging
from app.services.infrastructure.pre_filter_backfill import run_prefilter_backfill


def _print_summary(details: List[dict], limit: int = 25) -> None:
    """Render a concise table of flagged job reviews."""
    if not details:
        print("No reviews require updates.")
        return

    print("\nFlagged Reviews:")
    print("=" * 80)
    for item in details[:limit]:
        status = "UPDATED" if item.get("applied") else "PENDING"
        print(
            f"{item['job_id']} | {item['title']} @ {item['company']}\n"
            f"  Reason: {item['reason']}\n"
            f"  Status: {status}\n"
        )

    remaining = len(details) - limit
    if remaining > 0:
        print(f"… {remaining} additional record(s) omitted. Use --limit to narrow the scan.")


async def main() -> None:
    """Async entry point."""
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Reapply structured pre-filter rules to existing job_reviews rows",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist updates. Defaults to dry-run mode when omitted.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of recommended reviews to inspect (processes all by default).",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show the full list of flagged reviews instead of truncating the summary.",
    )

    args = parser.parse_args()

    logger.info(
        "Starting pre-filter backfill (apply_changes={apply}, limit={limit})",
        apply=args.apply,
        limit=args.limit,
    )

    result = await run_prefilter_backfill(apply=args.apply, limit=args.limit)

    print("Candidate reviews scanned:", result["candidates_scanned"])
    print("Pre-filter violations:", result["violations"])
    if args.apply:
        print("Reviews updated:", result["updated"])
    else:
        print("Dry run complete. Re-run with --apply to persist these changes.")

    summary_limit = len(result["details"]) if args.show_all else 25
    _print_summary(result["details"], limit=summary_limit)

    if result["violations"] and not args.apply:
        print("\nNext steps: run `python pre_filter_backfill.py --apply` after reviewing the summary.")


if __name__ == "__main__":
    asyncio.run(main())
