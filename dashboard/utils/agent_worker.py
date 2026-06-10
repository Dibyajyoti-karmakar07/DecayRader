"""
dashboard/utils/agent_worker.py
───────────────────────────────
Background agent worker that processes customers in a daemon thread.
Runs independently of the Streamlit page lifecycle.

Architecture:
  - The worker runs in a daemon thread spawned once per agent run.
  - All state is stored in a plain dict (WorkerState) that is referenced
    by both the thread and st.session_state.
  - The UI reads from WorkerState to display progress.
  - The UI writes WorkerState["stopped"] = True to terminate.
  - Python's GIL ensures dict reads/writes are atomic for simple types.
"""

from __future__ import annotations

import time
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


def create_worker_state(customers: list[dict], total: int) -> dict[str, Any]:
    """Create a fresh shared state dict for a new agent run."""
    return {
        # Control flags
        "running": True,
        "stopped": False,
        "finished": False,

        # Progress
        "current_idx": 0,
        "total": total,
        "phase": "idle",           # idle | processing | ready | waiting_review
        "processing_step": 0,

        # Customer data
        "customers": customers,
        "current_customer": None,
        "gemini_result": None,

        # Previous customer (for dimmed card display)
        "prev_customer": None,
        "prev_result": None,

        # Counters
        "saved_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "already_count": 0,

        # Logs
        "logs": [],

        # Toast queue
        "toast": None,

        # Thread reference
        "_thread": None,
    }


def _process_one_customer(
    state: dict,
    gemini_client: Any,
    db: Any,
) -> None:
    """Process a single customer: call Gemini and store result."""
    from agent.gemini_client import call_gemini
    from agent.agent_runner import anonymize_customer

    idx = state["current_idx"]
    customer = state["customers"][idx]

    # Update state for UI
    state["current_customer"] = customer
    state["gemini_result"] = None
    state["phase"] = "processing"
    state["processing_step"] = 0

    if state["stopped"]:
        return

    # Anonymize and call Gemini
    state["processing_step"] = 3  # "Gemini API called"
    state["phase"] = "calling"

    if state["stopped"]:
        return

    anon = anonymize_customer(customer)
    result = call_gemini(gemini_client, anon)

    if state["stopped"]:
        return

    state["processing_step"] = 4  # "Parsing response"

    if result is None:
        state["logs"].append(
            f"❌ {customer.get('company_name')} ({customer.get('customer_id')}) — Gemini API failed"
        )
        state["failed_count"] += 1
        state["current_idx"] += 1
        return

    # Store result and wait for human review
    state["gemini_result"] = result
    state["phase"] = "waiting_review"
    state["processing_step"] = 5  # "Ready for review"


def run_agent_loop(
    state: dict,
    gemini_client: Any,
    db: Any,
) -> None:
    """
    Main agent loop. Runs in a daemon thread.
    Processes customers one at a time, pausing for human review.
    """
    try:
        total = state["total"]

        while state["current_idx"] < total and not state["stopped"]:
            _process_one_customer(state, gemini_client, db)

            if state["stopped"]:
                break

            # If Gemini failed, the index was already advanced — loop again.
            if state["phase"] != "waiting_review":
                # Small sleep to avoid tight loop on consecutive failures
                time.sleep(0.5)
                continue

            # Wait for human to approve/skip this customer.
            # The UI sets phase to "advance" after the user clicks an action.
            while state["phase"] == "waiting_review" and not state["stopped"]:
                time.sleep(0.3)

            if state["stopped"]:
                break

            # After review, the UI has already advanced current_idx.
            # Small delay between customers for rate limiting
            time.sleep(1.0)

    except Exception as e:
        logger.error(f"Agent worker error: {e}", exc_info=True)
        state["logs"].append(f"💥 Worker error: {str(e)}")
    finally:
        state["running"] = False
        state["finished"] = True
        state["phase"] = "idle"
        logger.info("Agent worker thread finished.")


def start_worker(
    state: dict,
    gemini_client: Any,
    db: Any,
) -> threading.Thread:
    """Spawn the agent worker as a daemon thread."""
    t = threading.Thread(
        target=run_agent_loop,
        args=(state, gemini_client, db),
        daemon=True,
        name="decayrader-agent-worker",
    )
    state["_thread"] = t
    t.start()
    logger.info("Agent worker thread started.")
    return t


def stop_worker(state: dict) -> None:
    """Signal the worker to stop."""
    state["stopped"] = True
    state["running"] = False
    state["finished"] = True
    state["phase"] = "idle"
    logger.info("Agent worker stop requested.")


def approve_current(state: dict, action: str | None, db: Any) -> None:
    """
    Called by the UI when the user approves or skips the current customer.
    Saves the intervention to MongoDB, then signals the worker to advance.
    """
    from agent.mcp_actions import save_intervention

    customer = state["current_customer"]
    result = state["gemini_result"]

    if action and result is not None:
        # pyrefly: ignore [unexpected-keyword]
        success = save_intervention(db, customer, result, chosen_action=action)
        if success:
            state["saved_count"] += 1
            state["logs"].append(
                f"✅ {customer.get('company_name')} ({customer.get('customer_id')}) — {action}"
            )
            state["toast"] = {
                "action": action,
                "customer_name": customer.get("company_name", ""),
            }
        else:
            state["failed_count"] += 1
            state["logs"].append(
                f"⚠️ {customer.get('company_name')} ({customer.get('customer_id')}) — failed to save"
            )
    else:
        state["skipped_count"] += 1
        state["logs"].append(
            f"⏭️  {customer.get('company_name')} ({customer.get('customer_id')}) — skipped by user"
        )

    # Save previous for dimmed card
    state["prev_customer"] = customer
    state["prev_result"] = result

    # Advance index and signal the worker to continue
    state["current_idx"] += 1
    state["phase"] = "advance"
