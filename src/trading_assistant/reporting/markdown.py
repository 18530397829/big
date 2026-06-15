def bullet_list(items: list[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)
