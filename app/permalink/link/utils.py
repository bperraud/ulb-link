from xml.etree import ElementTree as ET
from urllib.parse import unquote


def webdav_to_jstree(xml, username):
    ns = {"d": "DAV:"}
    root = ET.fromstring(xml)
    base = f"/remote.php/dav/files/{username}/"
    nodes = []

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

        # Root folder
        if rel_path == "":
            path = "/"
            name = username
            parent = "#"
        else:
            path = "/" + rel_path
            name = rel_path.split("/")[-1]

            # Compute parent correctly
            parent_path = "/" + rel_path.rsplit("/", 1)[0] if "/" in rel_path else "/"
            parent = parent_path

        nodes.append({"id": path, "parent": parent, "text": name})

    return {"data": nodes}
