from urllib.parse import urlparse

def extract_pr_id_from_coolify_url(coolify_url: str) -> int | None:
    parsed = urlparse(coolify_url)
    hostname = parsed.hostname or ""
    f = hostname.split(".")[0]
    candidate = f.split("-")[0]
    return int(candidate) if candidate.isdigit() else None