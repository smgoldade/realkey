import micropip


# Keeps build123d from pulling the wrong ones
print("[BG] Mocking cadquery-ocp-novtk and lib3mf")
micropip.add_mock_package("cadquery-ocp-novtk", "7.9.3.1", modules={})
micropip.add_mock_package("lib3mf", "2.4.1", modules={})

# Install the required packages.
print("[BG] Installing packages - cadquery-ocp-novtk")
await micropip.install("cadquery-ocp-novtk-OCP.wasm==7.9.3.1.post202606201016", keep_going=True)
print("[BG] Installing packages - lib3mf")
await micropip.install("lib3mf-OCP.wasm==2.5.0.post202606200901", keep_going=True)
print("[BG] Installing packages - cadquery_ocp_proxy")
await micropip.install("cadquery_ocp_proxy==7.9.3.1.1", keep_going=True)
print("[BG] Installing packages - build123d")
await micropip.install("build123d==0.11.0", keep_going=True)
print("[BG] Installing packages - typing-extensions")
await micropip.install("typing-extensions", keep_going=True)
print("[BG] Packages installed")

import binascii
from build123d import *
from realkey import key, resource_fetcher, assa, dom, miwa, opnus, paclock, sargentandgreenleaf, schlage, vsr, follower


def shared_generate(part: Part) -> dict[str, str]:
    export_stl(part, "temp.stl")
    export_step(part, "temp.step")

    returns: dict[str, str] = {}
    with open("temp.stl", "rb") as stl:
        returns["stl"] = binascii.b2a_base64(stl.read()).decode("utf-8")
    with open("temp.step", "rb") as step:
        returns["step"] = binascii.b2a_base64(step.read()).decode("utf-8")

    return returns


def generate_key(key_tag: str, profile: str, keyway: str, bitting: str) -> dict[str, str]:
    key_class: key.Key = key.Key._list[key_tag]

    try:
        generated_key: Part | None = None
        if len(bitting) == 0:
            generated_key = key_class.blank(profile, keyway)
        else:
            generated_key = key_class.key(profile, keyway, bitting)
        if generated_key is None:
            return {"error": "No key or blank generated!"}

        return shared_generate(generated_key)
    except Exception as e:
        return {"error": f"{e}"}


def generate_key_art(key_tag: str, profile: str, keyway: str, bitting: str) -> dict[str, str]:
    key_class: key.Key = key.Key._list[key_tag]

    try:
        generated_key: Part | None = None
        if len(bitting) == 0:
            generated_key = key_class.blank(profile, keyway)
        else:
            generated_key = key_class.key(profile, keyway, bitting)
        if generated_key is None:
            return {"error": "No key or blank generated!"}

        view_port_origin = (100, 50, 80)
        visible, hidden = generated_key.project_to_viewport(view_port_origin)
        max_dimension = max(*Compound(children=visible + hidden).bounding_box().size)
        exporter = ExportSVG(scale=100 / max_dimension)
        exporter.add_layer("Visible")
        exporter.add_layer("Hidden", line_color=(99, 99, 99), line_type=LineType.ISO_DOT)
        exporter.add_shape(visible, layer="Visible")
        exporter.add_shape(hidden, layer="Hidden")
        exporter.write("temp.svg")

        returns: dict[str, str] = {}
        with open("temp.svg", "rb") as svg:
            returns["svg"] = binascii.b2a_base64(svg.read()).decode("utf-8")

        return returns
    except Exception as e:
        return {"error": f"{e}"}


def generate_follower(length: float, diameter: float, top_tag: str, top_config: dict[str, float], bottom_tag: str, bottom_config: dict[str, float]) -> dict[str, str]:
    try:
        generated_follower = follower.Follower.generate(follower.FollowerConfigData(length, diameter, top_tag, top_config.to_py(), bottom_tag, bottom_config.to_py()))
        if generate_follower is None:
            return {"error": "No follower generated!"}

        return shared_generate(generated_follower)

    except Exception as e:
        return {"error": f"{e.__class__.__name__} : {e}"}


def set_base_url(base_url: str):
    resource_fetcher.set_base_url(base_url)


__export__ = ["generate_key", "generate_follower", "set_base_url"]
