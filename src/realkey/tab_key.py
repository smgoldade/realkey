from pyscript import web, when

from realkey import key, tab, web_core, web_main, assa, dom, miwa, opnus, paclock, sargentandgreenleaf, schlage, vsr

key_select = web_core.SelectElement(web.page["key-select"])
profile_select = web_core.SelectElement(web.page["profile-select"])
keyway_select = web_core.SelectElement(web.page["keyway-select"])
show_advanced = web_core.Element(web.page["show-advanced"])
bitting_instructions = web_core.Element(web.page["bitting-instructions"])
bitting = web_core.StringValueElement(web.page["bitting"])
advanced_bitting_info = web_core.Element(web.page["advanced-bitting-info"])


def get_selected_key() -> key.Key | None:
    key_tag = key_select.selected_value
    if key_tag == "null":
        return None

    return key.Key._list[key_tag]


def run_validation():
    selected_key = get_selected_key()
    if selected_key is None:
        web_main.info.html = ""
        web_main.generate.enabled = False
        return
    if len(bitting.stripped_value) == 0:
        web_main.info.html = ""
        web_main.generate.enabled = True
        return
    try:
        selected_key.validate_bitting(profile_select.selected_value, keyway_select.selected_value, bitting.stripped_value)
        web_main.info.html = ""
        web_main.generate.enabled = True
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

    def show(self):
        super().show()
        run_validation()

    def get_query_params(self) -> dict[str, str]:
        return_values: dict[str, str] = {}

        if key_select.selected_value == "null":
            return return_values
        return_values["key"] = key_select.selected_value
        return_values["profile"] = profile_select.selected_value
        return_values["keyway"] = keyway_select.selected_value
        return_values["bitting"] = bitting.stripped_value

        return return_values

    def load_from_params(self, query_params):
        def set_key(key: str):
            key_select.selected_value = key
            key_change()

        if not self._populate_param(query_params, "key", set_key):
            return

        def set_profile(profile: str):
            profile_select.selected_value = profile
            profile_change()

        self._populate_param(query_params, "profile", set_profile)

        def set_keyway(keyway: str):
            keyway_select.selected_value = keyway
            keyway_change()

        self._populate_param(query_params, "keyway", set_keyway)

        def set_bitting(bittin: str):
            bitting.value = bittin

        self._populate_param(query_params, "bitting", set_bitting)

    async def generate(self, bg_worker) -> dict[str, str]:
        selected_key = get_selected_key()
        if selected_key is None:
            return {"error": "No key selected"}

        gen_keys = (await bg_worker.generate_key(selected_key.tag(), profile_select.selected_value, keyway_select.selected_value, bitting.stripped_value)).to_py()  # type: ignore
        if "error" in gen_keys:
            return gen_keys

        gen_keys["description"] = get_pretty_name()
        gen_keys["roughness"] = 0.25
        gen_keys["metalness"] = 0.95

        return gen_keys
