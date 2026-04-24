from xml.etree import ElementTree as ET
from urllib.parse import unquote

from link.models import Link, User


def is_folder(resp, ns):
    resourcetype = resp.find("d:propstat/d:prop/d:resourcetype", ns)
    if resourcetype is not None:
        return resourcetype.find("d:collection", ns) is not None
    return False


def webdav_to_jstree(xml, user: User):
    ns = {"d": "DAV:"}
    root = ET.fromstring(xml)
    base = f"/remote.php/dav/files/{user.username}/"
    nodes = []

    paths = Link.objects.filter(user=user, share__isnull=False).values_list(
        "share__path", flat=True
    )

    for resp in root.findall("d:response", ns):
        href_el = resp.find("d:href", ns)
        if href_el is None:
            continue

        href = href_el.text
        # Extract relative path
        if not href.startswith(base):
            continue

        rel_path = href[len(base) :]  # remove prefix
        rel_path = unquote(rel_path).rstrip("/")

        folder = is_folder(resp, ns)

        # Root folder
        if rel_path == "":
            path = "/"
            name = user.username
            parent = "#"
        else:
            path = "/" + rel_path
            name = rel_path.split("/")[-1]

            # Compute parent correctly
            parent_path = "/" + rel_path.rsplit("/", 1)[0] if "/" in rel_path else "/"
            parent = parent_path

        if path not in paths or folder:
            nodes.append(
                {
                    "id": path,
                    "parent": parent,
                    "text": name,
                    "icon": "jstree-folder" if folder else "jstree-file",
                }
            )

    return {"data": nodes}
