from permalink.settings import SITE_DOMAIN
from permalink.settings import SITE_PROTOCOL


def get_host():
    domain = SITE_DOMAIN
    if domain == "localhost":
        domain = "localhost:8080"

    return f"{SITE_PROTOCOL}://{domain}/token"


def host(request):
    return {"HOST": get_host()}
