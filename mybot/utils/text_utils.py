def sanitize_text(value: str | None) -> str | None:
    """Remove characters that cannot be encoded in UTF-8."""
    if value is None:
        return None
    return value.encode("utf-8", "ignore").decode("utf-8", "ignore")

