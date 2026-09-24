ISO_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS"Z"'


def iso(column: str) -> str:
    return f"to_char({column} AT TIME ZONE 'UTC', '{ISO_FORMAT}')"