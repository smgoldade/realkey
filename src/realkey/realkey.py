from pyscript import document, web, when
from pyscript.ffi import to_js
from js import URL, Blob, load_key


from realkey.Common import key
from realkey.ASSA import ASSA
from realkey.MIWA import MIWA
from realkey.Opnus import Opnus
from realkey.Paclock import Paclock
from typing import Callable

from build123d import *

generated_key: Part | None

key_select: web.ElementCollection = web.page["key-select"]
profile_select: web.ElementCollection = web.page["profile-select"]
keyway_select: web.ElementCollection = web.page["keyway-select"]
bitting_instructions: web.ElementCollection = web.page["bitting-instructions"]
bitting: web.ElementCollection = web.page["bitting"]
generate: web.ElementCollection = web.page["generate"]
preview: web.ElementCollection = web.page["preview"]
save_stl = web.page["save-stl"]
save_step = web.page["save-step"]
info = web.page["info"]

def main():
    remove_loading()
    load_keys()

def remove_loading():
    #defaults
    global profile_select, keyway_select, bitting_instructions, bitting, generate, preview, save_stl, save_step, info
    
    disable_element(key_select)
    disable_element(profile_select)
    disable_element(keyway_select)
    disable_element(bitting)
    bitting_instructions.innerHTML = ""
    bitting.value = "" 
    disable_element(generate)
    disable_element(preview)
    disable_element(save_stl)
    disable_element(save_step)
    info.innerHTML = ""

    loader = web.page["loader"]
    loader.remove()

def load_keys():
    global key_select
    populate_select(key_select, "Choose a key", {k : v.display_name() for k,v in key.Key._list.items()})
    enable_element(key_select)

def get_selected_key() -> key.Key | None:
    global key_select
    key_tag = key_select.options.selected.value
    if key_tag == "null" or key_tag == None: return None

    return key.Key._list[key_tag]

def get_selected_profile() -> str:
    global profile_select
    return str(profile_select.options.selected.value)

def get_selected_keyway() -> str:
    global keyway_select
    return str(keyway_select.options.selected.value)

def get_bitting() -> str:
    global bitting
    return str(bitting.value)

def is_preview() -> bool:
    global preview
    return bool(preview.checked)

@when("change", "#key-select")
def load_profiles_and_keyways():
    global profile_select, keyway_select, bitting_instructions, bitting, generate, preview, info, save_stl, save_step
    selected_key = get_selected_key()
    info.innerHTML = ""

    if selected_key == None:
        populate_select(profile_select, "No profiles loaded...", {})
        populate_select(keyway_select, "No keyways loaded...", {})
        bitting_instructions.innerHTML = ""
        bitting.value = ""
        disable_element(profile_select)
        disable_element(keyway_select)
        disable_element(bitting)
        disable_element(generate)
        disable_element(preview)
        disable_element(save_stl)
        disable_element(save_step)
        return

    populate_select(profile_select, "", selected_key.profiles())
    populate_select(keyway_select, "", selected_key.keyways())
    bitting_instructions.innerHTML = selected_key.cut_definition()
    bitting.value = ""
    enable_element(profile_select)
    enable_element(keyway_select)
    enable_element(bitting)
    enable_element(generate)
    enable_element(preview)

@when("keydown", "#bitting")
def bitting_change():
    global save_stl, save_step, info
    disable_element(save_stl)
    disable_element(save_step)
    info.innerHTML = ""

@when("click", "#generate")
def generate_key():
    global generated_key, generate, preview, save_stl, save_step, info
    disable_element(generate)
    disable_element(preview)
    disable_element(save_stl)
    disable_element(save_step)   

    selected_key = get_selected_key()
    if selected_key == None: return

    info.innerHTML = "Generating key, please wait as this may take a while..."
    profile = get_selected_profile()
    keyway = get_selected_keyway()
    bitting = get_bitting()

    try:
        generated_key = selected_key.key(profile, keyway, bitting)
    except Exception as e:
        info.innerHTML = "<span style='color:#800'>" + str(e) + "</span>"
        enable_element(generate)
        enable_element(preview)
        return

    if is_preview():
        info.innerHTML = "Generating model..."
        export_stl(generated_key, "temp.stl")
        open_file = open("temp.stl", "rb")
        stl_bytes = to_js(open_file.read())
        stl_blob = Blob.new([stl_bytes], {type: "model/stl"})
        url = URL.createObjectURL(stl_blob)
        load_key(url)
        URL.revokeObjectURL(url)
    info.innerHTML = "<span style='color:#080;'>Generated</span>"

    enable_element(generate)
    enable_element(preview)
    enable_element(save_stl)
    enable_element(save_step)

def save_shared(file_extension: str, core_func: Callable):
    global generated_key, generate, preview, save_stl, save_step, info
    disable_element(generate)
    disable_element(preview)
    disable_element(save_stl)
    disable_element(save_step)

    key = str(key_select.options.selected.innerHTML)
    profile = str(profile_select.options.selected.innerHTML)
    keyway = str(keyway_select.options.selected.innerHTML)
    bitting = get_bitting()

    info.innerHTML = "Generating model file..."

    core_func()

    open_file = open("temp." + file_extension, "rb")
    stl_bytes = to_js(open_file.read())
    stl_blob = Blob.new([stl_bytes], {type: "model/" + file_extension})
    url = URL.createObjectURL(stl_blob)

    hidden_link = document.createElement("a")
    hidden_link.setAttribute("download", key + " - " + profile + " - " + keyway + " - " + bitting + "." + file_extension)
    hidden_link.setAttribute("href", url)
    hidden_link.click()

    URL.revokeObjectURL(url)

    enable_element(generate)
    enable_element(preview)
    enable_element(save_stl)
    enable_element(save_step)

@when("click", "#save-stl")
def save_as_stl():
    global generated_key
    if generated_key == None: return
    save_shared("stl", lambda : export_stl(generated_key, "temp.stl"))

@when("click", "#save-step")
def save_as_step():
    global generated_key
    if generated_key == None: return
    save_shared("step", lambda : export_step(generated_key, "temp.step"))


def populate_select(select_element: web.ElementCollection, null_string: str, dict: dict[str,str]):
    select_element.options.clear()
    if len(null_string) > 0:
        select_element.options.add(value = "null", html = null_string)
    
    for value, html in dict.items():
        select_element.options.add(value = value, html = html)

def enable_element(element: web.ElementCollection):
    element.removeAttribute("disabled")

def disable_element(element: web.ElementCollection):
    element.disabled = True

def uncheck_element(element: web.ElementCollection):
    element.removeAttribute("checked")