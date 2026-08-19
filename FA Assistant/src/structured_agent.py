"""Structured-data agent: reads client profiles, accounts, and holdings from data/clients.json."""
from __future__ import annotations

import json

from . import config


def _load_clients() -> list[dict]:
    with open(config.CLIENTS_FILE) as f:
        return json.load(f)


def _find_client(client_id: str) -> dict | None:
    client_id = client_id.strip().upper()
    for client in _load_clients():
        if client["client_id"].upper() == client_id:
            return client
    return None


def list_clients() -> list[dict]:
    """Return a lightweight list of every client (id, name, risk tolerance)."""
    return [
        {
            "client_id": c["client_id"],
            "name": c["name"],
            "risk_tolerance": c["risk_tolerance"],
        }
        for c in _load_clients()
    ]


def get_client_profile(client_id: str) -> dict:
    """Return a client's full profile: demographics, goals, notes, and account balances."""
    client = _find_client(client_id)
    if client is None:
        return {"error": f"No client found with client_id '{client_id}'"}

    accounts_summary = [
        {"account_type": a["account_type"], "balance": a["balance"]}
        for a in client["accounts"]
    ]
    return {
        "client_id": client["client_id"],
        "name": client["name"],
        "age": client["age"],
        "risk_tolerance": client["risk_tolerance"],
        "annual_income": client["annual_income"],
        "net_worth": client["net_worth"],
        "investment_goals": client["investment_goals"],
        "advisor_notes": client["advisor_notes"],
        "accounts": accounts_summary,
        "total_invested_assets": sum(a["balance"] for a in client["accounts"]),
    }


def get_client_holdings(client_id: str) -> dict:
    """Return the detailed account-by-account holdings (tickers, shares, cost basis) for a client."""
    client = _find_client(client_id)
    if client is None:
        return {"error": f"No client found with client_id '{client_id}'"}

    return {
        "client_id": client["client_id"],
        "name": client["name"],
        "accounts": client["accounts"],
    }
