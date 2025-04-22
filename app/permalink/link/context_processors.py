from permalink.settings import SITE_DOMAIN
from permalink.settings import SITE_PROTOCOL


def host(request):
    return {"HOST": f"{SITE_PROTOCOL}://{SITE_DOMAIN}/token"}
