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
