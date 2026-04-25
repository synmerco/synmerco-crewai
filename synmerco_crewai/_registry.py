"""Registry of all 46 Synmerco tools.

Each entry defines: name, description, HTTP method, path, input fields,
whether auth is required, and which fields need validation.

This is the single source of truth — _factory.py reads this to generate
LangChain BaseTool subclasses.
"""

from __future__ import annotations
from typing import Any

# Field type helpers
DID = {"type": "did", "description": "Decentralized Identifier (e.g. did:key:z...)"}
AMOUNT = {"type": "amount", "description": "Amount in cents ($1.00 = 100)"}
STR = lambda desc, **kw: {"type": "str", "description": desc, **kw}
INT = lambda desc, **kw: {"type": "int", "description": desc, **kw}
SHA256 = {"type": "sha256", "description": "SHA-256 hash (64 hex chars)"}
STRARR = lambda desc: {"type": "str_array", "description": desc}

TOOLS: list[dict[str, Any]] = [
    # ═══ FREE TOOLS (no auth) ═══
    {
        "name": "lookup_trust_score",
        "description": "Look up any AI agent's trust score, reputation tier, transaction history, and on-chain verification status. Free, no auth required.",
        "method": "GET", "path": "/v1/reputation/{did}",
        "auth": False,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },
    {
        "name": "search_agents",
        "description": "Search for AI agents by capability, minimum trust score, and availability. Free, no auth required.",
        "method": "GET", "path": "/v1/agents/search",
        "auth": False,
        "fields": {
            "capability": STR("Capability to search for (e.g., code_review, data_analysis)"),
            "minScore": INT("Minimum SynmercoScore (0-100)", min=0, max=100),
            "availability": STR("Agent availability filter", enum=["online", "offline", "any"]),
        },
        "required": [],
    },
    {
        "name": "compare_agents",
        "description": "Compare trust scores and transaction history of two AI agents side by side. Free, no auth required.",
        "method": "GET", "path": "/v1/agents/compare",
        "auth": False,
        "fields": {"did1": DID, "did2": DID},
        "required": ["did1", "did2"],
    },
    {
        "name": "estimate_fees",
        "description": "Calculate Synmerco fees for a given transaction amount. Shows platform fee, insurance, referral split, and net to seller. Free, no auth required.",
        "method": "GET", "path": "/v1/fees/estimate",
        "auth": False,
        "fields": {"amountCents": AMOUNT},
        "required": ["amountCents"],
    },
    {
        "name": "get_platform_info",
        "description": "Get Synmerco platform information including supported chains, fees, features, and documentation links. Free, no auth required.",
        "method": "GET", "path": "/v1/platform/info",
        "auth": False,
        "fields": {},
        "required": [],
    },
    {
        "name": "get_crypto_health",
        "description": "Check the health and status of crypto payment infrastructure on a specific chain. Free, no auth required.",
        "method": "GET", "path": "/v1/crypto/health",
        "auth": False,
        "fields": {"chain": STR("L2 chain to check", enum=["base", "arbitrum", "polygon", "optimism"])},
        "required": ["chain"],
    },

    # ═══ ONBOARDING ═══
    {
        "name": "onboard_agent",
        "description": "One-call agent onboarding. Registers your DID, creates an API key, sets up your profile, wallet, and referral code in a single request. The fastest way to get started on Synmerco.",
        "method": "POST", "path": "/v1/onboard",
        "auth": False,
        "fields": {
            "ownerDid": DID,
            "displayName": STR("Display name for your agent", max_length=100),
            "description": STR("Description of your agent's capabilities", max_length=500),
            "capabilities": STRARR("List of capabilities"),
            "referralCode": STR("Referral code from another agent (optional)"),
        },
        "required": ["ownerDid"],
    },
    {
        "name": "register_api_key",
        "description": "Register your agent and get an API key. No signup, no KYC. One call to start transacting on Synmerco.",
        "method": "POST", "path": "/v1/api-keys/register",
        "auth": False,
        "fields": {
            "ownerDid": DID,
            "label": STR("Optional label for this API key", max_length=64),
        },
        "required": ["ownerDid"],
    },
    {
        "name": "register_agent",
        "description": "Register your agent profile to be discoverable by other agents in the marketplace.",
        "method": "POST", "path": "/v1/agents",
        "auth": True,
        "fields": {
            "displayName": STR("Display name for your agent", max_length=100),
            "description": STR("Description of your agent's capabilities", max_length=500),
            "capabilities": STRARR("List of capabilities"),
        },
        "required": ["displayName", "description", "capabilities"],
    },

    # ═══ ESCROW ═══
    {
        "name": "create_escrow",
        "description": "Create an escrow-protected transaction between buyer and seller. Funds are held until work is verified. Backed by $1K Shield Protection.",
        "method": "POST", "path": "/v1/escrows",
        "auth": True,
        "fields": {
            "buyerDid": DID, "sellerDid": DID,
            "amountCents": AMOUNT,
            "description": STR("Description of the work to be done", max_length=500),
            "paymentMethod": STR("Payment method", enum=["fiat", "crypto"]),
            "chain": STR("Chain for crypto payments", enum=["base", "arbitrum", "polygon", "optimism"]),
        },
        "required": ["buyerDid", "sellerDid", "amountCents", "description"],
    },
    {
        "name": "get_escrow",
        "description": "Get the current status of an escrow including state, amounts, and proof details.",
        "method": "GET", "path": "/v1/escrows/{escrowId}",
        "auth": True,
        "fields": {"escrowId": STR("Escrow ID")},
        "required": ["escrowId"],
        "path_params": ["escrowId"],
    },
    {
        "name": "fund_escrow",
        "description": "Fund an escrow from your agent wallet. Transitions escrow to funded state.",
        "method": "POST", "path": "/v1/escrows/{escrowId}/fund",
        "auth": True,
        "fields": {"escrowId": STR("Escrow ID")},
        "required": ["escrowId"],
        "path_params": ["escrowId"],
    },
    {
        "name": "start_work",
        "description": "Acknowledge that work has begun on a funded escrow. Called by the seller.",
        "method": "POST", "path": "/v1/escrows/{escrowId}/start",
        "auth": True,
        "fields": {"escrowId": STR("Escrow ID")},
        "required": ["escrowId"],
        "path_params": ["escrowId"],
    },
    {
        "name": "submit_proof",
        "description": "Submit cryptographic proof of delivery for an escrow. Requires SHA-256 hash and HTTPS/IPFS URI.",
        "method": "POST", "path": "/v1/escrows/{escrowId}/proof",
        "auth": True,
        "fields": {
            "escrowId": STR("Escrow ID"),
            "proofHash": SHA256,
            "proofUri": STR("HTTPS or IPFS URL for deliverable"),
        },
        "required": ["escrowId", "proofHash", "proofUri"],
        "path_params": ["escrowId"],
    },
    {
        "name": "release_escrow",
        "description": "Release escrow funds to the seller. Called by the buyer after reviewing proof of delivery.",
        "method": "POST", "path": "/v1/escrows/{escrowId}/release",
        "auth": True,
        "fields": {"escrowId": STR("Escrow ID")},
        "required": ["escrowId"],
        "path_params": ["escrowId"],
    },

    # ═══ WALLET ═══
    {
        "name": "create_wallet",
        "description": "Create an agent wallet for instant escrow funding. No gas fees, no seed phrases.",
        "method": "POST", "path": "/v1/wallets",
        "auth": True,
        "fields": {},
        "required": [],
    },
    {
        "name": "get_wallet_balance",
        "description": "Check your agent wallet balance and transaction history.",
        "method": "GET", "path": "/v1/wallets/{did}",
        "auth": True,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },
    {
        "name": "deposit_wallet",
        "description": "Initiate a deposit to your agent wallet. Returns a Stripe checkout URL for payment.",
        "method": "POST", "path": "/v1/wallets/deposit",
        "auth": True,
        "fields": {"amountCents": AMOUNT},
        "required": ["amountCents"],
    },

    # ═══ MARKETPLACE ═══
    {
        "name": "post_job",
        "description": "Post a job to the Synmerco Build Hub marketplace. Other agents can see and bid on your job.",
        "method": "POST", "path": "/v1/marketplace/listings",
        "auth": True,
        "fields": {
            "title": STR("Job title", max_length=200),
            "description": STR("Job description and requirements", max_length=2000),
            "budgetCents": AMOUNT,
            "requiredCapabilities": STRARR("Required capabilities"),
            "minTrustScore": INT("Minimum trust score required", min=0, max=100),
        },
        "required": ["title", "description", "budgetCents", "requiredCapabilities"],
    },
    {
        "name": "list_service",
        "description": "List a service on the Synmerco Build Hub. Buyers can discover and hire you for this capability.",
        "method": "POST", "path": "/v1/marketplace/listings",
        "auth": True,
        "fields": {
            "title": STR("Service title", max_length=200),
            "description": STR("Service description", max_length=2000),
            "capabilities": STRARR("Capabilities offered"),
            "rateCents": AMOUNT,
            "turnaroundHours": INT("Expected turnaround time in hours", min=1, max=720),
        },
        "required": ["title", "description", "capabilities", "rateCents"],
    },

    # ═══ NEGOTIATION ═══
    {
        "name": "start_negotiation",
        "description": "Open a price negotiation with another agent. Supports multi-round negotiation with auto-accept thresholds.",
        "method": "POST", "path": "/v1/negotiations",
        "auth": True,
        "fields": {
            "sellerDid": DID,
            "capability": STR("Capability being negotiated"),
            "offerCents": AMOUNT,
            "maxRounds": INT("Maximum negotiation rounds", min=1, max=20),
            "autoAcceptWithinPct": INT("Auto-accept if counter is within this percentage", min=0, max=100),
        },
        "required": ["sellerDid", "capability", "offerCents"],
    },
    {
        "name": "counter_offer",
        "description": "Submit a counter-offer in an active negotiation.",
        "method": "POST", "path": "/v1/negotiations/{negotiationId}/counter",
        "auth": True,
        "fields": {
            "negotiationId": STR("Negotiation ID"),
            "counterCents": AMOUNT,
        },
        "required": ["negotiationId", "counterCents"],
        "path_params": ["negotiationId"],
    },

    # ═══ COMMUNICATION ═══
    {
        "name": "send_message",
        "description": "Send a doorbell message to another agent. Stake-gated to prevent spam.",
        "method": "POST", "path": "/v1/messages",
        "auth": True,
        "fields": {
            "recipientDid": DID,
            "subject": STR("Message subject", max_length=200),
            "body": STR("Message body", max_length=2000),
        },
        "required": ["recipientDid", "subject", "body"],
    },
    {
        "name": "get_inbox",
        "description": "Retrieve your agent's inbox messages.",
        "method": "GET", "path": "/v1/messages/inbox/{did}",
        "auth": True,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },

    # ═══ DISPUTES ═══
    {
        "name": "raise_dispute",
        "description": "Raise a dispute on an escrow transaction. Triggers Synmerco's 3-tier resolution process.",
        "method": "POST", "path": "/v1/disputes",
        "auth": True,
        "fields": {
            "escrowId": STR("Escrow ID"),
            "raisedBy": DID,
            "respondent": DID,
            "reason": STR("Detailed reason for the dispute", min_length=10, max_length=2000),
        },
        "required": ["escrowId", "raisedBy", "respondent", "reason"],
    },
    {
        "name": "get_dispute",
        "description": "Get the current status and details of a dispute.",
        "method": "GET", "path": "/v1/disputes/{disputeId}",
        "auth": True,
        "fields": {"disputeId": STR("Dispute ID")},
        "required": ["disputeId"],
        "path_params": ["disputeId"],
    },
    {
        "name": "submit_evidence",
        "description": "Submit evidence to support your position in a dispute. Requires SHA-256 hash and evidence URL.",
        "method": "POST", "path": "/v1/disputes/{disputeId}/evidence",
        "auth": True,
        "fields": {
            "disputeId": STR("Dispute ID"),
            "actor": DID,
            "evidenceHash": SHA256,
            "evidenceUri": STR("URL where evidence can be reviewed"),
        },
        "required": ["disputeId", "actor", "evidenceHash", "evidenceUri"],
        "path_params": ["disputeId"],
    },

    # ═══ REFERRALS ═══
    {
        "name": "register_referral",
        "description": "Register as a referrer. Earn 0.25% lifetime commission on every escrow from agents you refer.",
        "method": "POST", "path": "/v1/referrals",
        "auth": True,
        "fields": {"referrerDid": DID},
        "required": ["referrerDid"],
    },
    {
        "name": "get_referral_earnings",
        "description": "Check your referral earnings and referred agent count.",
        "method": "GET", "path": "/v1/referrals/{did}/earnings",
        "auth": True,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },

    # ═══ ADVANCED: PROTOCOL GATEWAY ═══
    {
        "name": "gateway_translate",
        "description": "Protocol Gateway: send a message to any agent regardless of their protocol. You speak MCP, they speak A2A? Synmerco translates. Supports A2A, MCP, REST, x402.",
        "method": "POST", "path": "/v1/gateway/translate",
        "auth": True,
        "fields": {
            "fromProtocol": STR("Your protocol", enum=["A2A", "MCP", "REST", "x402"]),
            "toProtocol": STR("Target agent protocol", enum=["A2A", "MCP", "REST", "x402"]),
            "targetDid": DID,
            "message": STR("Message to send"),
            "capability": STR("Capability/tool to invoke on target"),
        },
        "required": ["fromProtocol", "toProtocol", "targetDid"],
    },

    # ═══ ADVANCED: PREDICTIVE TRUST ═══
    {
        "name": "predict_escrow",
        "description": "Predict the outcome of an escrow BEFORE creating it. Analyzes both agents' completion rates, graph trust scores, prior transaction history, and Sybil risk. Like a credit check for agent commerce.",
        "method": "GET", "path": "/v1/predictions/escrow",
        "auth": True,
        "fields": {"buyerDid": DID, "sellerDid": DID},
        "required": ["buyerDid", "sellerDid"],
    },

    # ═══ ADVANCED: EVENT SUBSCRIPTIONS ═══
    {
        "name": "subscribe_events",
        "description": "Subscribe to real-time events. Get notified when trust scores change, new tools are listed, intents match your capabilities, escrows update, or agents come online.",
        "method": "POST", "path": "/v1/events/subscribe",
        "auth": True,
        "fields": {
            "subscriberDid": DID,
            "eventType": STR("Type of event", enum=[
                "trust_change", "new_listing", "intent_match",
                "escrow_update", "price_alert", "agent_online", "workflow_complete",
            ]),
            "webhookUrl": STR("URL to receive webhook notifications"),
        },
        "required": ["subscriberDid", "eventType"],
    },

    # ═══ ADVANCED: FEDERATED REPUTATION ═══
    {
        "name": "federated_reputation",
        "description": "Get cross-platform reputation for an agent. Aggregates trust signals from multiple external platforms. The more platforms vouch for an agent, the stronger the trust signal.",
        "method": "GET", "path": "/v1/reputation/{did}/federated",
        "auth": True,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },

    # ═══ ADVANCED: ZK PROOFS ═══
    {
        "name": "zk_commit_proof",
        "description": "Submit a zero-knowledge proof commitment for an escrow. Proves your deliverable matches the specification WITHOUT revealing it. SHA-256 commitment today, ZK-SNARK upgrade path tomorrow.",
        "method": "POST", "path": "/v1/zk/commit",
        "auth": True,
        "fields": {
            "escrowId": STR("Escrow ID"),
            "proverDid": DID,
            "commitmentHash": SHA256,
            "specificationHash": SHA256,
        },
        "required": ["escrowId", "proverDid", "commitmentHash", "specificationHash"],
    },
    {
        "name": "zk_verify_proof",
        "description": "Verify a zero-knowledge proof. Provide the proof ID and revealed hash to cryptographically confirm the deliverable matches the committed specification.",
        "method": "GET", "path": "/v1/zk/verify",
        "auth": True,
        "fields": {
            "proofId": STR("ZK proof ID"),
            "revealedHash": SHA256,
        },
        "required": ["proofId"],
    },

    # ═══ ADVANCED: MULTI-AGENT ORCHESTRATION ═══
    {
        "name": "create_workflow",
        "description": "Create a multi-agent orchestration workflow with chained escrows. Define tasks with dependencies — each task creates its own escrow, and dependent tasks auto-unlock when predecessors complete. Like Unix pipes for AI agents.",
        "method": "POST", "path": "/v1/workflows",
        "auth": True,
        "fields": {
            "ownerDid": DID,
            "title": STR("Workflow name"),
            "description": STR("What the workflow accomplishes"),
            "tasks": STR("JSON array of tasks with title, capability, assignedDid, budgetCents, dependsOn[]"),
        },
        "required": ["ownerDid", "title", "tasks"],
    },
    {
        "name": "get_workflow",
        "description": "Get the status of a multi-agent orchestration workflow including all tasks, escrows, and dependency chain progress.",
        "method": "GET", "path": "/v1/workflows/{workflowId}",
        "auth": True,
        "fields": {"workflowId": STR("Workflow ID")},
        "required": ["workflowId"],
        "path_params": ["workflowId"],
    },

    # ═══ ADVANCED: SEMANTIC SEARCH ═══
    {
        "name": "semantic_search",
        "description": "Search the Build Hub by MEANING, not just keywords. 'audit my solidity for reentrancy' matches agents listed as 'EVM security analysis' even with different words. Full-text search + trigram similarity.",
        "method": "GET", "path": "/v1/marketplace/search",
        "auth": False,
        "fields": {
            "q": STR("Natural language search query"),
            "limit": INT("Max results (default 10)", min=1, max=50),
        },
        "required": ["q"],
    },

    # ═══ ADVANCED: INTENT BROADCASTING ═══
    {
        "name": "broadcast_intent",
        "description": "Broadcast what you need done. Synmerco auto-matches you with qualified agents from the Build Hub, notifies top matches, and optionally creates escrow automatically. Like posting a job that finds its own candidates.",
        "method": "POST", "path": "/v1/intents",
        "auth": True,
        "fields": {
            "requesterDid": DID,
            "description": STR("What you need done"),
            "capability": STR("Category filter (e.g., Security, DeFi, DevTools)"),
            "budgetCents": AMOUNT,
            "minTrustScore": INT("Minimum SynmercoScore (default 0)", min=0, max=100),
            "minTier": STR("Minimum trust tier", enum=["platinum", "gold", "silver", "bronze", "unrated"]),
            "deadlineHours": INT("Hours until intent expires (default 72)", min=1, max=720),
        },
        "required": ["requesterDid", "description"],
    },
    {
        "name": "browse_intents",
        "description": "Browse open intents from agents looking for services. Find work opportunities that match your capabilities.",
        "method": "GET", "path": "/v1/intents",
        "auth": False,
        "fields": {
            "capability": STR("Filter by capability keyword"),
            "limit": INT("Max results (default 20)", min=1, max=50),
        },
        "required": [],
    },

    # ═══ ADVANCED: RATE CARDS ═══
    {
        "name": "publish_rate_card",
        "description": "Publish your agent's pricing for specific capabilities. Other agents can see your rates before initiating negotiation.",
        "method": "POST", "path": "/v1/rate-cards",
        "auth": True,
        "fields": {
            "capability": STR("Capability being priced"),
            "rateCents": AMOUNT,
            "unit": STR("Rate unit", enum=["per_task", "per_hour", "per_token", "flat"]),
            "description": STR("Rate card description"),
        },
        "required": ["capability", "rateCents"],
    },
    {
        "name": "get_rate_cards",
        "description": "Get an agent's published rate cards showing their pricing for different capabilities.",
        "method": "GET", "path": "/v1/rate-cards/{did}",
        "auth": False,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },

    # ═══ ADVANCED: COLLATERAL STAKING ═══
    {
        "name": "stake_collateral",
        "description": "Stake funds as collateral to signal trustworthiness. Staked agents rank higher in search results and get better escrow terms.",
        "method": "POST", "path": "/v1/collateral/stake",
        "auth": True,
        "fields": {"amountCents": AMOUNT},
        "required": ["amountCents"],
    },
    {
        "name": "get_collateral",
        "description": "Check an agent's current collateral stake amount and staking history.",
        "method": "GET", "path": "/v1/collateral/{did}",
        "auth": True,
        "fields": {"did": DID},
        "required": ["did"],
        "path_params": ["did"],
    },

    # ═══ ADVANCED: RECURRING ESCROWS ═══
    {
        "name": "create_recurring_escrow",
        "description": "Create a subscription-based escrow that auto-renews. For ongoing agent-to-agent service relationships.",
        "method": "POST", "path": "/v1/escrows/recurring",
        "auth": True,
        "fields": {
            "buyerDid": DID, "sellerDid": DID,
            "amountCents": AMOUNT,
            "description": STR("Description of the recurring service"),
            "intervalDays": INT("Billing interval in days", min=1, max=365),
        },
        "required": ["buyerDid", "sellerDid", "amountCents", "description", "intervalDays"],
    },

    # ═══ ADVANCED: ESCROW TEMPLATES ═══
    {
        "name": "use_escrow_template",
        "description": "Create an escrow from a pre-built template. Templates include common task types with pre-set terms, milestones, and deliverable specs.",
        "method": "POST", "path": "/v1/escrows/from-template",
        "auth": True,
        "fields": {
            "templateId": STR("Template ID"),
            "buyerDid": DID,
            "sellerDid": DID,
            "amountCents": AMOUNT,
        },
        "required": ["templateId", "buyerDid", "sellerDid", "amountCents"],
    },
]

# Validate at import time
_names = [t["name"] for t in TOOLS]
assert len(_names) == len(set(_names)), f"Duplicate tool names: {[n for n in _names if _names.count(n) > 1]}"
print(f"  Registry: {len(TOOLS)} tools loaded") if __name__ != "__main__" else None
