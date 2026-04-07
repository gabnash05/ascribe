class NonRetryableError(Exception):
    """Raised for failures where retrying will never succeed."""
