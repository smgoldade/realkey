import pathlib
import sys

if sys.platform == "emscripten":
    from pyodide.http import pyxhr

_base_url: str = ""
_PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
_WEB_PACKAGE_PATH = "src/realkey"


def set_base_url(base_url: str):
    global _base_url
    _base_url = base_url


def fetch_resource(resource: str) -> str | None:
    """Return a usable local path, downloading browser resources as needed."""
    resource_path = pathlib.Path(resource)
    if resource_path.is_file():
        return str(resource_path.resolve())

    if sys.platform != "emscripten":
        package_resource_path = _PACKAGE_ROOT / resource_path
        if package_resource_path.is_file():
            return str(package_resource_path.resolve())
        return None

    if not _base_url:
        raise AttributeError("No Base URL has been set for resource fetching!")

    fetch_path = f"{_base_url}/{_WEB_PACKAGE_PATH}/{resource}"
    resource_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {fetch_path}")
    response = pyxhr.get(fetch_path)
    if response.ok:
        data = response._xhr.response

        with resource_path.open("wb") as r:
            r.write(data.encode("utf-8"))
        return str(resource_path.resolve())
    return None
