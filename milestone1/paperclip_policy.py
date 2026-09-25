"""Create an issue policy for Paperclip; never track workflow state here."""

from uuid import UUID


def _agent_id(value: str) -> str:
    try:
        parsed = UUID(value)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid Paperclip agent ID: {value!r}") from exc
    if str(parsed) != value.lower():
        raise ValueError(f"invalid Paperclip agent ID: {value!r}")
    return str(parsed)


def engineering_execution_policy(
    developer_agent_id: str,
    validator_agent_id: str,
    reviewer_agent_id: str,
    approver_user_id: str,
    *,
    qa_agent_id: str | None = None,
) -> dict:
    """Map distinct roles to ordered native Paperclip stages at issue creation.

    The assigned Developer is passed only to enforce independence; assignment,
    transitions, review decisions, and retries remain Paperclip-owned.
    """
    agents = [_agent_id(agent_id) for agent_id in (developer_agent_id, validator_agent_id, reviewer_agent_id)]
    if qa_agent_id is not None:
        agents.append(_agent_id(qa_agent_id))
    if len(set(agents)) != len(agents):
        raise ValueError("Developer, validator, Reviewer and QA must be distinct Paperclip agents")
    if not isinstance(approver_user_id, str) or not approver_user_id.strip():
        raise ValueError("integration approver user ID must be nonempty")

    stages = [
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[1]}]},
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[2]}]},
    ]
    if qa_agent_id is not None:
        stages.append({"type": "review", "participants": [{"type": "agent", "agentId": agents[3]}]})
    stages.append({"type": "approval", "participants": [{"type": "user", "userId": approver_user_id}]})
    return {"mode": "normal", "commentRequired": True, "maxReviewRounds": 3, "stages": stages}
