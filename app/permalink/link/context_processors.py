from permalink.settings import SITE_DOMAIN, SITE_PROTOCOL


def get_host():
    return f"{SITE_PROTOCOL}://{SITE_DOMAIN}"


def host(request):
    return {"HOST": get_host()}
