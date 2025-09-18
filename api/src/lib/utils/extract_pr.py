from urllib.parse import urlparse

def extract_pr_id_from_coolify_url(hostname: str) -> int | None:
    parsed = urlparse(hostname)
    hostname = parsed.hostname or ""
    f = hostname.split(".")[0]
    candidate = f.split("-")[0]
    return int(candidate) if candidate.isdigit() else None