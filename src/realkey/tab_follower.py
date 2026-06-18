from pyscript import web, when
from pyscript.ffi import to_js
from realkey import follower, tab, web_core, web_main

follower_select = web_core.SelectElement(web.page["follower-select"])
follower_length = web_core.LengthInputElement(web.page["follower-length"])
follower_diameter = web_core.LengthInputElement(web.page["follower-diameter"])
follower_top_select = web_core.SelectElement(web.page["follower-top-select"])
follower_top_div = web_core.Element(web.page["follower-top-div"])
follower_bottom_select = web_core.SelectElement(web.page["follower-bottom-select"])
follower_bottom_div = web_core.Element(web.page["follower-bottom-div"])

top_elements: dict[str, web_core.FloatValueElement] = {}
bottom_elements: dict[str, web_core.FloatValueElement] = {}


def run_validation():
    web_main.info.html = ""
    web_main.generate.enabled = True


def load_follower():
    selected_tag = follower_select.selected_value

    config = follower.FOLLOWER_DEFINITIONS[selected_tag]
    if config is None:
        return

    follower_length.value = config.length
    follower_diameter.value = config.diameter
    follower_top_select.selected_value = config.top_tag
    load_follower_end(True, config.top_tag, config.top_config)
    follower_bottom_select.selected_value = config.bottom_tag
    load_follower_end(False, config.bottom_tag, config.bottom_config)


def load_follower_end(is_top: bool, tag: str, config: None | dict[str, float]):
    div_element = follower_top_div if is_top else follower_bottom_div
    elements = top_elements if is_top else bottom_elements
    follower_end: follower.FollowerEnd = follower.FollowerEnd._list[tag]
    follower_config = follower_end.config()

    div_element._web_element.replaceChildren()  # type: ignore
    elements.clear()
    if not follower_config:
        return

    def create_element(is_top: bool, tag: str, label: str):
        id = tag + "-ig-" + ("top" if is_top else "bottom")
        p = web.p()
        l = web.label(htmlFor=id, innerHTML=label)
        s = web.span(id=id)
        p.append(l, web.br(), s)
        return p

    id = "rotation-ig-" + ("top" if is_top else "bottom")
    p = web.p()
    l = web.label(htmlFor=id, innerHTML="Rotation")
    s = web.input_(id=id, type="text", value="0")
    p.append(l, web.br(), s, web.span(" deg"))
    div_element._web_element.append(p)  # type: ignore
    elements["rotation"] = web_core.FloatValueElement(web.page[id])

    for tag, label in follower_config.items():
        div_element._web_element.append(create_element(is_top, tag, label))  # type: ignore
        id = tag + "-ig-" + ("top" if is_top else "bottom")
        input = web_core.LengthInputElement(web.page[id])
        elements[tag] = input
        when("change", input._get_input())(end_value_change)
        if config and tag in config:
            input.value = config[tag]


@when("change", "#follower-select")
def follower_change():
    load_follower()
    run_validation()


@when("change", "#follower-length")
def length_change():
    follower_select.selected_value = "Custom"
    run_validation()


@when("change", "#follower-diameter")
def diameter_change():
    follower_select.selected_value = "Custom"
    run_validation()


@when("change", "#follower-top-select")
def top_change():
    follower_select.selected_value = "Custom"
    load_follower_end(True, follower_top_select.selected_value, None)
    run_validation()


@when("change", "#follower-bottom-select")
def bottom_change():
    follower_select.selected_value = "Custom"
    load_follower_end(False, follower_bottom_select.selected_value, None)
    run_validation()


def end_value_change():
    follower_select.selected_value = "Custom"
    run_validation()


def get_pretty_name() -> str:
    if follower_select.selected_value == "Custom":
        return f"Custom Follower - {follower_length.stripped_value}mm x {follower_diameter.stripped_value}mm - {follower_top_select.selected_html} ({",".join([f"{v.stripped_value}mm" for v in top_elements.values()])}) - {follower_bottom_select.selected_html} ({",".join([f"{v.stripped_value}mm" for v in bottom_elements.values()])})"
    else:
        return f"{follower_select.selected_value} Follower"


class FollowerTab(tab.Tab):
    def __init__(self, button: web_core.Element, tab: web_core.Element) -> None:
        super().__init__(button, tab)

        follower_select.populate("", {"": {k: k for k in follower.FOLLOWER_DEFINITIONS.keys()}})
        follower_select.enabled = True

        follower_top_select.populate("", {"": {k: v.display_name() for k, v in follower.FollowerEnd._list.items()}})
        follower_top_select.enabled = True

        follower_bottom_select.populate("", {"": {k: v.display_name() for k, v in follower.FollowerEnd._list.items()}})
        follower_bottom_select.enabled = True

    def show(self):
        super().show()
        run_validation()

    def get_query_params(self) -> dict[str, str]:
        return_values: dict[str, str] = {}

        return_values["follower"] = follower_select.selected_value
        if "Custom" != return_values["follower"]:
            return return_values

        return_values["follower_length"] = str(follower_length.stripped_value)
        return_values["follower_diameter"] = str(follower_diameter.stripped_value)
        return_values["follower_top"] = follower_top_select.selected_value
        for tag, element in top_elements.items():
            return_values[tag + "-ig-top"] = str(element.stripped_value)
        return_values["follower_bottom"] = follower_bottom_select.selected_value
        for tag, element in bottom_elements.items():
            return_values[tag + "-ig-bottom"] = str(element.stripped_value)

        return return_values

    def load_from_params(self, query_params):
        def set_follower(follower: str):
            follower_select.selected_value = follower
            follower_change()

        self._populate_param(query_params, "follower", set_follower)

        if "Custom" != follower_select.selected_value:
            return

        def set_follower_length(length: str):
            follower_length.value = float(length)
            length_change()

        self._populate_param(query_params, "follower_length", set_follower_length)

        def set_follower_diameter(diameter: str):
            follower_diameter.value = float(diameter)
            length_change()

        self._populate_param(query_params, "follower_diameter", set_follower_diameter)

        def set_follower_top(top: str):
            follower_top_select.selected_value = top
            top_change()

            for tag, element in top_elements.items():

                def set_element_value(value: str):
                    element.value = float(value)

                self._populate_param(query_params, tag + "-ig-top", set_element_value)

        self._populate_param(query_params, "follower_top", set_follower_top)

        def set_follower_bottom(bottom: str):
            follower_bottom_select.selected_value = bottom
            bottom_change()

            for tag, element in bottom_elements.items():

                def set_element_value(value: str):
                    element.value = float(value)

                self._populate_param(query_params, tag + "-ig-bottom", set_element_value)

        self._populate_param(query_params, "follower_bottom", set_follower_bottom)

    async def generate(self, bg_worker) -> dict[str, str]:
        top_config: dict[str, float] = {}
        for tag, element in top_elements.items():
            top_config[tag] = element.stripped_value

        bottom_config: dict[str, float] = {}
        for tag, element in bottom_elements.items():
            bottom_config[tag] = element.stripped_value

        gen_follower = (
            await bg_worker.generate_follower(
                follower_length.stripped_value,
                follower_diameter.stripped_value,
                follower_top_select.selected_value,
                top_config,
                follower_bottom_select.selected_value,
                bottom_config,
            )
        ).to_py()  # type: ignore
        if "error" in gen_follower:
            return gen_follower

        gen_follower["description"] = get_pretty_name()
        gen_follower["roughness"] = 0.25
        gen_follower["metalness"] = 0.95
        gen_follower["color"] = 0xC0C0C0

        return gen_follower
