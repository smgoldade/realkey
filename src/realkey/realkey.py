from pyscript import document, web, when, workers
from pyscript.ffi import to_js
from pyscript.js_modules import key3d
from js import URL, Blob

import base64
from realkey.Common import key
from realkey.ASSA import ASSA
from realkey.MIWA import MIWA
from realkey.Opnus import Opnus
from realkey.Paclock import Paclock
from typing import Callable

from build123d import *

key_select: web.ElementCollection = web.page["key-select"]
profile_select: web.ElementCollection = web.page["profile-select"]
keyway_select: web.ElementCollection = web.page["keyway-select"]
bitting_instructions: web.ElementCollection = web.page["bitting-instructions"]
bitting: web.ElementCollection = web.page["bitting"]
generate: web.ElementCollection = web.page["generate"]
save_stl = web.page["save-stl"]
save_step = web.page["save-step"]
info = web.page["info"]
model_overlay = web.page["model-overlay"]

keygen = None
stl_blob : Blob = None
step_blob : Blob = None # Help me step blob Im stuck

def main(bg_keygen):
    global keygen
    keygen = bg_keygen
    remove_loading()
    load_keys()

def remove_loading():
    #defaults
    global profile_select, keyway_select, bitting_instructions, bitting, generate, save_stl, save_step, info, model_overlay
    
    disable_element(key_select)
    disable_element(profile_select)
    disable_element(keyway_select)
    disable_element(bitting)
    bitting_instructions.innerHTML = ""
    bitting.value = "" 
    disable_element(generate)
    disable_element(save_stl)
    disable_element(save_step)
    info.innerHTML = ""
    model_overlay.innerHTML = ""

    key3d.loadKey("resources/realkey.stl")
    loader = web.page["loader"]
    loader.remove()

def load_keys():
    global key_select
    populate_select(key_select, "Choose a key", {k : v.display_name() for k,v in key.Key._list.items()})
    enable_element(key_select)

def get_selected_key() -> key.Key | None:
    global key_select
    key_tag = key_select.options.selected.value
    if key_tag == "null" or key_tag is None: return None

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

@when("change", "#key-select")
def load_profiles_and_keyways():
    global profile_select, keyway_select, bitting_instructions, bitting, generate, info, model_overlay, save_stl, save_step
    selected_key = get_selected_key()
    info.innerHTML = ""
    model_overlay.innerHTML = ""

    if selected_key is None:
        populate_select(profile_select, "No profiles loaded...", {})
        populate_select(keyway_select, "No keyways loaded...", {})
        bitting_instructions.innerHTML = ""
        bitting.value = ""
        disable_element(profile_select)
        disable_element(keyway_select)
        disable_element(bitting)
        disable_element(generate)
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

@when("keyup", "#bitting")
def bitting_change():
    global info

    selected_key = get_selected_key()
    if selected_key is None: return
    try:
        profile = get_selected_profile()
        keyway = get_selected_keyway()
        bitting = get_bitting()
        selected_key.validate_bitting(profile, keyway, bitting)
        info.innerHTML = ""
    except Exception as e:
        info.innerHTML = f"<span style='color:#800'>{e}</span>"
    

@when("click", "#generate")
async def generate_key():
    global generate, preview, save_stl, save_step, info, model_overlay, keygen, stl_blob, step_blob
    disable_element(generate)
    disable_element(save_stl)
    disable_element(save_step)   

    selected_key = get_selected_key()
    if selected_key is None: return

    model_overlay.innerHTML = "Generating..."
    profile = get_selected_profile()
    keyway = get_selected_keyway()
    bitting = get_bitting()

    gen_keys= (await keygen.generate_key(selected_key.name(), profile, keyway, bitting)).to_py()
    if "error" in gen_keys:
        decoded_error = gen_keys["error"]
        info.innerHTML = f"<span style='color:#800'>{decoded_error}</span>"
        return

    stl_bytes = base64.b64decode(gen_keys["stl"])
    step_bytes = base64.b64decode(gen_keys["step"])
    stl_blob = Blob.new([to_js(stl_bytes)],{type: "model/stl"})
    step_blob = Blob.new([to_js(step_bytes)], {type: "model/step"})

    stl_url = URL.createObjectURL(stl_blob)
    key3d.loadKey(stl_url)
    URL.revokeObjectURL(stl_url)
    model_overlay.innerHTML = ""
    
    enable_element(generate)
    enable_element(save_stl)
    enable_element(save_step)

def save_shared(blob, extension: str):
    global key_select

    key = str(key_select.options.selected.innerHTML)
    profile = get_selected_profile()
    keyway = get_selected_keyway()
    bitting = get_bitting()

    url = URL.createObjectURL(blob)
    hidden_link = document.createElement("a")
    hidden_link.setAttribute("download", f"{key}_{profile}_{keyway}_{bitting}.{extension}")
    hidden_link.setAttribute("href", url)
    hidden_link.click()
    URL.revokeObjectURL(url)


@when("click", "#save-stl")
def save_as_stl():
    global stl_blob
    if stl_blob is None: return

    save_shared(stl_blob, "stl")

@when("click", "#save-step")
def save_as_step():
    global step_blob
    if step_blob is None: return

    save_shared(step_blob, "step")


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