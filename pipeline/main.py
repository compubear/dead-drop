"""Dead Drop Pipeline — Main entry point."""

import argparse
import sys

import structlog

from pipeline.config import settings

logger = structlog.get_logger()


def setup_logging() -> None:
    """Configure structured logging with JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.dev.ConsoleRenderer()
                if settings.APP_ENV == "development"
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def run_pipeline(run_once: bool = False) -> None:
    """Execute the full pipeline cycle."""
    logger.info("pipeline.starting", env=settings.APP_ENV, run_once=run_once)

    if run_once:
        logger.info("pipeline.run_once", status="starting")

        # === STEP 1: Source Monitoring ===
        from pipeline.sources.orchestrator import run_monitoring_cycle

        logger.info("pipeline.step", step="1_source_monitoring")
        monitor_result = run_monitoring_cycle()
        logger.info(
            "pipeline.step_complete",
            step="1_source_monitoring",
            items_found=monitor_result.items_found,
            sources_ok=monitor_result.sources_successful,
            sources_fail=monitor_result.sources_failed,
        )

        # === STEP 2: Gap Detection ===
        # Note: Requires CLAUDE_API_KEY to be set
        logger.info("pipeline.step", step="2_gap_detection")
        if settings.CLAUDE_API_KEY:
            from pipeline.gap_detection.scorer import score_items_batch, select_top_stories

            # Collect all items from the monitoring cycle as dicts
            # In production these come from DB; for now from the orchestrator
            logger.info("pipeline.gap_detection", status="scoring")
            # scored = score_items_batch(items, min_gap_score=3.0)
            # top_stories = select_top_stories(scored, max_stories=5)
            logger.info("pipeline.gap_detection", status="api_key_present_but_no_items_to_score")
        else:
            logger.warning("pipeline.gap_detection", status="skipped_no_api_key")

        # === STEP 3: Verification ===
        logger.info("pipeline.step", step="3_verification")
        logger.info("pipeline.verification", status="awaiting_scored_stories")

        # === STEP 4: Content Generation ===
        logger.info("pipeline.step", step="4_content_generation")
        logger.info("pipeline.content_gen", status="awaiting_verified_stories")

        logger.info("pipeline.run_once", status="complete")
    else:
        logger.info("pipeline.scheduled", cron=settings.PIPELINE_SCHEDULE_CRON)
        # TODO: Start scheduled pipeline with APScheduler or similar
        logger.info("pipeline.scheduled", status="waiting_for_trigger")



def main() -> None:
    """CLI entry point for the Dead Drop pipeline."""
    parser = argparse.ArgumentParser(
        description="Dead Drop — AI Content Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the pipeline once and exit (no scheduling)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Dead Drop Pipeline v{__import__('pipeline').__version__}",
    )

    args = parser.parse_args()
    setup_logging()

    try:
        run_pipeline(run_once=args.run_once)
    except KeyboardInterrupt:
        logger.info("pipeline.shutdown", reason="keyboard_interrupt")
        sys.exit(0)
    except Exception as exc:
        logger.exception("pipeline.fatal_error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
