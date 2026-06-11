from pyscript import web, when
from pyscript.ffi import to_js
from js import Blob, URL
from pyscript.js_modules import model_view  # type: ignore

from realkey import key, tab, web_core, web_main, ASSA, DOM, MIWA, Opnus, Paclock, SargentAndGreenleaf, Schlage
import binascii, urllib.parse

key_select = web_core.SelectElement(web.page["key-select"])
profile_select = web_core.SelectElement(web.page["profile-select"])
keyway_select = web_core.SelectElement(web.page["keyway-select"])
show_advanced = web_core.Element(web.page["show-advanced"])
bitting_instructions = web_core.Element(web.page["bitting-instructions"])
bitting = web_core.ValueElement(web.page["bitting"])
advanced_bitting_info = web_core.Element(web.page["advanced-bitting-info"])


def get_selected_key() -> key.Key | None:
    key_tag = key_select.selected_value
    if key_tag == "null":
        return None

    return key.Key._list[key_tag]


def run_validation():
    if len(bitting.stripped_value) == 0:
        return
    selected_key = get_selected_key()
    if selected_key is None:
        return
    try:
        selected_key.validate_bitting(profile_select.selected_value, keyway_select.selected_value, bitting.stripped_value)
        web_main.generate.enabled = True
        web_main.info.html = ""
    except Exception as e:
        web_main.info.html = f"<span style='color:#800'>{e}</span>"
        web_main.generate.enabled = False


def load_profiles_and_keyways():
    selected_key = get_selected_key()
    web_main.info.html = ""
    web_main.model_generating.html = ""

    if selected_key is None:
        profile_select.populate("No profiles loaded...", {})
        keyway_select.populate("No keyways loaded...", {})
        show_advanced.hidden = True
        advanced_bitting_info.html = ""
        bitting_instructions.html = ""
        bitting.value = ""
        profile_select.enabled = False
        keyway_select.enabled = False
        bitting.enabled = False
        web_main.generate.enabled = False
        return

    web_main.meta_image.content = selected_key.artwork()
    profile_select.populate("", selected_key.profiles())
    keyway_select.populate("", selected_key.keyways())
    decode_definition = selected_key.advanced_bitting_definition()
    if decode_definition is not None:
        show_advanced.hidden = False
        advanced_bitting_info.html = decode_definition
    else:
        show_advanced.hidden = True
        advanced_bitting_info.html = ""
    bitting_instructions.html = selected_key.basic_bitting_definition()
    bitting.value = ""
    profile_select.enabled = True
    keyway_select.enabled = True
    bitting.enabled = True
    web_main.generate.enabled = True


@when("change", "#key-select")
def key_change():
    load_profiles_and_keyways()
    run_validation()


@when("change", "#profile-select")
def profile_change():
    run_validation()


@when("change", "#keyway-select")
def keyway_change():
    run_validation()


def get_pretty_name() -> str:
    return f"{key_select.selected_html} - {profile_select.selected_html} - {keyway_select.selected_html} - {bitting.stripped_value if len(bitting.stripped_value) > 0 else 'Blank'}"


@when("keyup", "#bitting")
def bitting_change():
    run_validation()


class KeyTab(tab.Tab):
    def __init__(self, button: web_core.Element, tab: web_core.Element) -> None:
        super().__init__(button, tab)

        key_select.enabled = False
        profile_select.enabled = False
        keyway_select.enabled = False
        bitting.enabled = False
        show_advanced.hidden = True
        advanced_bitting_info.html = ""
        bitting_instructions.html = ""
        bitting.value = ""

        key_select.populate("Choose a key", {"": {k: v.display_name() for k, v in key.Key._list.items()}})
        key_select.enabled = True

    def load_from_params(self, query_params):
        if "key" in query_params:
            target_key = urllib.parse.unquote(query_params.get("key"))
            for option in key_select.options:
                if option.value == target_key:
                    option.selected = True
                    load_profiles_and_keyways()
                    break
            else:
                return
        if "profile" in query_params:
            target_profile = urllib.parse.unquote(query_params.get("profile"))
            for option in profile_select.options:
                if option.value == target_profile:
                    option.selected = True
                    break
        if "keyway" in query_params:
            target_keyway = urllib.parse.unquote(query_params.get("keyway"))
            for option in keyway_select.options:
                if option.value == target_keyway:
                    option.selected = True
                    break
        if "bitting" in query_params:
            target_bitting = urllib.parse.unquote(query_params.get("bitting"))
            bitting.value = target_bitting

    async def generate(self, bg_worker) -> dict[str, str]:
        selected_key = get_selected_key()
        if selected_key is None:
            return {"error": "No key selected"}

        gen_keys = (await bg_worker.generate_key(selected_key.name(), profile_select.selected_value, keyway_select.selected_value, bitting.stripped_value)).to_py()  # type: ignore
        if "error" in gen_keys:
            return gen_keys

        gen_keys["description"] = get_pretty_name()
        gen_keys["roughness"] = 0.5
        gen_keys["metalness"] = 0.95

        return gen_keys
