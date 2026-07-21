"""Concurrency helpers for fanning out blocking (sync) I/O calls.

Runs a set of labelled *synchronous* callables concurrently by offloading each
to the AnyIO worker-thread pool, so the event loop stays free while the sync
integrations (httpx + sync SQLAlchemy logging) do their blocking work.

Failures are isolated per call: one failing/slow section never breaks the
others — each returns a :class:`SectionResult` describing its outcome.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Literal

import anyio

from apex_dashboard_analytics.core.logging import get_logger

logger = get_logger(__name__)

SectionStatus = Literal["ok", "error", "timeout"]


@dataclass
class SectionResult:
    """Outcome of a single fanned-out call."""

    status: SectionStatus
    data: Any | None = None
    error: str | None = None
    duration_ms: float | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


async def gather_sections(
    calls: dict[str, Callable[[], Any]],
    *,
    per_call_timeout: float,
    total_timeout: float,
) -> dict[str, SectionResult]:
    """Run ``calls`` concurrently in worker threads and collect results.

    Args:
        calls: mapping of section label -> zero-arg sync callable.
        per_call_timeout: seconds before an individual call is marked "timeout".
        total_timeout: overall wall-clock budget; calls unfinished when it
            elapses are marked "timeout".

    Returns:
        Mapping of the same labels to :class:`SectionResult`.

    Note:
        Cancelling a Python thread is not possible, so a timed-out call's
        underlying HTTP request keeps running until the integration's own httpx
        timeout stops it. ``per_call_timeout`` should therefore be >= the
        integration timeout to act as a genuine upper bound.
    """

    async def run(label: str, fn: Callable[[], Any]) -> tuple[str, SectionResult]:
        start = perf_counter()
        try:
            data = await asyncio.wait_for(
                anyio.to_thread.run_sync(fn), timeout=per_call_timeout
            )
            return label, SectionResult("ok", data=data, duration_ms=_elapsed_ms(start))
        except asyncio.TimeoutError:
            logger.warning("section_timeout", section=label)
            return label, SectionResult(
                "timeout", error="timed out", duration_ms=_elapsed_ms(start)
            )
        except Exception as exc:  # noqa: BLE001 - isolate per-section failures
            logger.warning("section_failed", section=label, error=repr(exc))
            return label, SectionResult(
                "error", error=repr(exc), duration_ms=_elapsed_ms(start)
            )

    tasks = [run(label, fn) for label, fn in calls.items()]
    try:
        pairs = await asyncio.wait_for(asyncio.gather(*tasks), timeout=total_timeout)
        return dict(pairs)
    except asyncio.TimeoutError:
        # Overall budget exceeded: report every section that didn't resolve.
        logger.warning("dashboard_total_timeout", total_timeout=total_timeout)
        return {
            label: SectionResult("timeout", error="overall budget exceeded")
            for label in calls
        }
