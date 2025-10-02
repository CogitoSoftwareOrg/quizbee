def cache_key(attempt_id: str):
    return f"attempt-{attempt_id}"


def cache_key_extra_body(attempt_id: str):
    return {"extra_body": {"prompt_cache_key": cache_key(attempt_id)}}
