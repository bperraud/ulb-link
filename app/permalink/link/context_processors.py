from permalink.settings import SITE_DOMAIN
from permalink.settings import SITE_PROTOCOL

def get_host():
    return f"{SITE_PROTOCOL}://{SITE_DOMAIN}/t"

def host(request):
    return {"HOST": get_host()}
