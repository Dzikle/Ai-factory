"""Offline cross-reference checks; Paperclip remains the runtime policy authority."""


def check_consistency(vocabulary: dict, roles: dict, project: dict, skills: list[dict]) -> list[str]:
    """Report invalid policy references without creating or granting runtime profiles."""
    errors: list[str] = []
    definitions: dict[str, dict] = {}
    for capability in vocabulary["capabilities"]:
        capability_id = capability["id"]
        if capability_id in definitions:
            errors.append(f"duplicate capability definition {capability_id}")
        definitions[capability_id] = capability

    def check_references(owner: str, values: list[str], *, allowed: bool) -> None:
        for capability_id in values:
            definition = definitions.get(capability_id)
            if definition is None:
                errors.append(f"{owner} {'allows' if allowed else 'denies'} undefined capability {capability_id}")
            elif allowed and definition["lifecycle"] in {"disabled", "deprecated"}:
                errors.append(f"{owner} allows {definition['lifecycle']} capability {capability_id}")

    for role_name, policy in roles["roles"].items():
        owner = f"role {role_name}"
        allowed = policy["allowed_capabilities"]
        denied = policy["denied_capabilities"]
        check_references(owner, allowed, allowed=True)
        check_references(owner, denied, allowed=False)
        for capability_id in sorted(set(allowed) & set(denied)):
            errors.append(f"{owner} both allows and denies {capability_id}")

    allowed = project["allowed_capabilities"]
    denied = project["denied_capabilities"]
    check_references("project", allowed, allowed=True)
    check_references("project", denied, allowed=False)
    for capability_id in sorted(set(allowed) & set(denied)):
        errors.append(f"project both allows and denies {capability_id}")

    for skill in skills:
        owner = f"skill {skill['skill']}"
        required = skill["required_capabilities"]
        optional = skill.get("optional_capabilities", [])
        denied = skill.get("denied_capabilities", [])
        check_references(owner, required, allowed=True)
        check_references(owner, optional, allowed=False)
        check_references(owner, denied, allowed=False)
        for capability_id in sorted((set(required) | set(optional)) & set(denied)):
            errors.append(f"{owner} both requests and denies {capability_id}")

        if skill["skill"] not in project["allowed_skills"]:
            continue
        project_grants = set(project["allowed_capabilities"]) - set(project["denied_capabilities"])
        for role_name in skill["roles"]:
            role = roles["roles"].get(role_name)
            if role is None:
                errors.append(f"{owner} names undefined role {role_name}")
                continue
            role_grants = set(role["allowed_capabilities"]) - set(role["denied_capabilities"])
            for capability_id in required:
                if capability_id not in project_grants:
                    errors.append(f"{owner} role {role_name} lacks required capability {capability_id} in project policy")
                if capability_id not in role_grants:
                    errors.append(f"{owner} role {role_name} lacks required capability {capability_id} in role policy")

    return errors


def check_context_budget(plan: dict) -> list[str]:
    """Reject a plan whose reserved query budgets exceed its hard package ceiling."""
    errors: list[str] = []
    if sum(query["max_tokens"] for query in plan["queries"]) > plan["total_budget"]["max_tokens"]:
        errors.append("query token budgets exceed total")
    if sum(query["max_bytes"] for query in plan["queries"]) > plan["total_budget"]["max_bytes"]:
        errors.append("query byte budgets exceed total")
    for query in plan["queries"]:
        if query["filters"]["project_id"] != plan["project_id"]:
            errors.append(f"query {query['domain']} escapes project {plan['project_id']}")
    return errors


def check_quality_independence(outcome: dict) -> list[str]:
    """Flag self-review evidence before a quality outcome can be accepted."""
    if outcome["kind"] not in {"review", "qa"}:
        return []
    errors: list[str] = []
    if outcome["actor_agent_id"] == outcome["subject_agent_id"]:
        errors.append(f"{outcome['kind']} actor must differ from implementer")
    if outcome["run_id"] == outcome["subject_run_id"]:
        errors.append(f"{outcome['kind']} run must differ from subject run")
    return errors


def check_task_request(request: dict, vocabulary: dict, roles: dict, project: dict, skills: list[dict]) -> list[str]:
    """Check task restrictions against Git policy; do not issue runtime grants."""
    errors: list[str] = []
    if request["project_id"] != project["project_id"]:
        errors.append("task project does not match overlay")
    role = roles["roles"].get(request["role"])
    if role is None:
        return errors + [f"task names undefined role {request['role']}"]

    definitions = {item["id"]: item for item in vocabulary["capabilities"]}
    available = (
        set(role["allowed_capabilities"])
        & set(project["allowed_capabilities"])
    ) - set(role["denied_capabilities"]) - set(project["denied_capabilities"]) - set(request["denied_capabilities"])

    for capability_id in request["required_capabilities"]:
        definition = definitions.get(capability_id)
        if capability_id not in available or definition is None or definition["lifecycle"] in {"disabled", "deprecated"}:
            errors.append(f"task requires unavailable capability {capability_id}")

    sidecars = {skill["skill"]: skill for skill in skills}
    for skill_id in request["skill_ids"]:
        skill = sidecars.get(skill_id)
        if skill is None or skill_id not in project["allowed_skills"] or request["role"] not in skill["roles"]:
            errors.append(f"task cannot use skill {skill_id}")
            continue
        for capability_id in skill["required_capabilities"]:
            if capability_id in request["denied_capabilities"]:
                errors.append(f"task denies required skill capability {capability_id}")
            elif capability_id not in available:
                errors.append(f"task cannot satisfy skill {skill_id} capability {capability_id}")
    return errors
