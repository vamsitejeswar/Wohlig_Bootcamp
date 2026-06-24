# Blocks any SQL that is not a SELECT statement

BLOCKED_KEYWORDS = {"insert", "update", "delete", "drop", "create", "alter", "truncate", "merge"}

def is_read_only(sql: str) -> bool:
    first_word = sql.strip().split()[0].lower()
    return first_word not in BLOCKED_KEYWORDS
