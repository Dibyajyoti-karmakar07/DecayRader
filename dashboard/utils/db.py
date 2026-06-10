"""
dashboard/utils/db.py
─────────────────────
Centralised MongoDB connection helper for the DecayRader dashboard.
"""

import os
import logging

import certifi
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
)

# ── Constants ────────────────────────────────────────────────────────────────
DATABASE_NAME = "DecayRader"
_CONNECTION_TIMEOUT_MS = 5_000

logger = logging.getLogger(__name__)


# ── Cached client (one pool per app lifetime) ───────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_mongo_client() -> MongoClient:
    """Return a cached MongoClient; created once and reused across reruns."""
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise EnvironmentError(
            "MONGODB_URI is not set. "
            "Add it to a .env file or export it as an environment variable."
        )
    return MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=_CONNECTION_TIMEOUT_MS,
    )


def connect_to_mongo():
    """Return a database handle for the *DecayRader* database.

    Returns
    -------
    pymongo.database.Database
        A handle to the ``DecayRader`` database.
    """
    client = _get_mongo_client()
    return client[DATABASE_NAME]


def check_connection() -> bool:
    """Ping the cluster. Returns True if healthy, False otherwise."""
    try:
        client = _get_mongo_client()
        client.admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as exc:
        logger.warning("MongoDB health-check failed: %s", exc)
        return False
    except EnvironmentError:
        logger.warning("MongoDB URI not configured.")
        return False


def get_db_stats() -> dict | None:
    """Return dbStats for DecayRader, or None on failure."""
    try:
        db = connect_to_mongo()
        stats = db.command("dbStats")
        collections = db.list_collection_names()
        counts = {}
        for col in collections:
            try:
                counts[col] = db[col].estimated_document_count()
            except Exception:
                counts[col] = 0
        return {
            "db_name": DATABASE_NAME,
            "collections": collections,
            "collection_count": len(collections),
            "document_counts": counts,
            "total_documents": sum(counts.values()),
            "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
            "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
        }
    except Exception as exc:
        logger.warning("Failed to fetch DB stats: %s", exc)
        return None
