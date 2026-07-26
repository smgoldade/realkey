import asyncio
import binascii
import html
import urllib.parse

from build123d import *
from js import Blob, URL, URLSearchParams, navigator, window  # type: ignore
from pyscript import document, web, when
from pyscript.ffi import to_js
from pyscript.js_modules import model_view  # type: ignore

from realkey import tab, tab_follower, tab_key, web_core

generate = web_core.Element(web.page["generate"])
save_stl = web_core.Element(web.page["save-stl"])
save_step = web_core.Element(web.page["save-step"])
copy_link = web_core.Element(web.page["copy-link"])
_info = web_core.Element(web.page["info"])
model_description = web_core.Element(web.page["model-description"])
_model_overlay_text = web_core.Element(web.page["model-overlay-text"])
about_dialog = web_core.DialogElement(web.page["about-dialog"])
share_dialog = web_core.DialogElement(web.page["share-dialog"])
share_settings = web_core.CheckboxElement(web.page["share-settings"])
share_generate = web_core.CheckboxElement(web.page["share-generate"])
toast = web_core.Element(web.page["toast"])

bg_worker = None
stl_blob: Blob = None
step_blob: Blob = None
toast_version = 0
generation_valid = False
generation_in_progress = False
auto_generate_pending = False
worker_load_failed = False

tabs: dict[str, tab.Tab] = {
    "key": tab_key.KeyTab(web_core.Element(web.page["key-tab-button"]), web_core.Element(web.page["key-tab"])),
    "follower": tab_follower.FollowerTab(web_core.Element(web.page["follower-tab-button"]), web_core.Element(web.page["follower-tab"])),
}


# UI state helpers
def set_info(text: str, is_error: bool = False):
    has_text = len(text) > 0
    _info._web_element.textContent = text
    _info._set_class_bool("info-message", has_text and not is_error)
    _info._set_class_bool("info-error", has_text and is_error)
    _info._web_element.setAttribute("role", "alert" if has_text and is_error else "status")  # type: ignore


def set_model_overlay_text(text: str = ""):
    if not text:
        _model_overlay_text.html = ""
        return

    _model_overlay_text.html = f"""<span class="generation-card">
        <span class="loading-spinner" aria-hidden="true"></span>
        <span>{html.escape(text)}</span>
    </span>"""


def clear_model_status():
    if not auto_generate_pending and not generation_in_progress:
        set_model_overlay_text()


def set_generation_valid(value: bool):
    global generation_valid
    generation_valid = value
    update_generation_availability()


def update_generation_availability():
    worker_loading = bg_worker is None
    generate._set_class_bool("worker-loading", worker_loading and not worker_load_failed)
    generate._set_class_bool("worker-failed", worker_load_failed)

    if worker_load_failed:
        generate.html = '<i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i> Model generator failed to load'
        generate.enabled = False
        return

    if worker_loading:
        generate.html = '<span class="loading-spinner loading-spinner-button" aria-hidden="true"></span> Model generator loading...'
        generate.enabled = False
        return

    generate.html = '<i class="fa-solid fa-cube"></i> Generate model'
    generate.enabled = generation_valid and not generation_in_progress


def update_download_availability():
    save_stl.enabled = stl_blob is not None
    save_step.enabled = step_blob is not None


# Application lifecycle
async def main():
    await remove_loading()
    await apply_search_params()


async def remove_loading():
    # defaults
    update_generation_availability()
    update_download_availability()
    set_info("")
    set_model_overlay_text()

    loader = web.page["loader"]
    try:
        await model_view.loadObject("src/realkey/resources/realkey.stl", 0.25, 0.95)
        model_description.html = "<i>Is this a real key?</i>"
    except Exception as error:
        set_info(f"Unable to load the initial model: {error}", True)
        model_description.html = "<i>Initial model preview unavailable.</i>"
    finally:
        loader.classes.add("hide")


async def background_worker_loaded(background_worker):
    global bg_worker, auto_generate_pending, worker_load_failed
    bg_worker = background_worker
    worker_load_failed = False
    update_generation_availability()

    was_auto_generate_pending = auto_generate_pending
    should_auto_generate = was_auto_generate_pending and generation_valid
    auto_generate_pending = False
    if should_auto_generate:
        await start_generation()
    elif was_auto_generate_pending:
        set_model_overlay_text()


def background_worker_failed():
    global worker_load_failed, auto_generate_pending
    worker_load_failed = True
    if auto_generate_pending:
        auto_generate_pending = False
        set_model_overlay_text()
        set_info("Automatic generation could not start because the model generator failed to load.", True)
    update_generation_availability()


async def apply_search_params():
    global auto_generate_pending
    query_params = URLSearchParams.new(window.location.search)

    # legacy links, assume tab is key
    target_tab = "key"
    if "tab" in query_params:
        target_tab = urllib.parse.unquote(query_params["tab"])
        if target_tab not in tabs.keys():
            target_tab = "key"

    for key, tab in tabs.items():
        if key == target_tab:
            tab.show()
            tab.load_from_params(query_params)
        else:
            tab.hide()

    if "generate" in query_params:
        generate_value = urllib.parse.unquote(query_params["generate"])

        if generate_value != "" and generate_value != "true":
            return
        if bg_worker is None:
            auto_generate_pending = True
            set_model_overlay_text("Waiting for the model generator to finish loading...")
        elif generation_valid:
            await start_generation()


# Tab navigation
def get_selected_tab() -> tuple[tab.Tab, str]:
    for tag, tab in tabs.items():
        if tab.selected:
            return (tab, tag)
    return tabs["key"], "key"


def change_to_tab(tab_key: str):
    for key, tab in tabs.items():
        if key == tab_key:
            tab.show()
        else:
            tab.hide()


@when("click", "#key-tab-button")
def change_to_key_tab():
    change_to_tab("key")


@when("click", "#follower-tab-button")
def change_to_follower_tab():
    change_to_tab("follower")


# Dialog controls
@when("click", "#show-about-dialog")
def show_about_dialog():
    about_dialog.show_modal()


@when("click", "#close-about-dialog")
def close_about_dialog():
    about_dialog.close()


@when("click", "#show-share-dialog")
def show_share_dialog():
    share_dialog.show_modal()


@when("click", "#close-share-dialog")
def close_share_dialog():
    share_dialog.close()


# Model generation
@when("click", "#generate")
async def start_generation():
    global generation_in_progress, stl_blob, step_blob
    if bg_worker is None or generation_in_progress or not generation_valid:
        return

    generation_in_progress = True
    update_generation_availability()
    update_download_availability()

    set_model_overlay_text("Generating model...")

    stl_url = None
    try:
        data = await get_selected_tab()[0].generate(bg_worker)
        if "error" in data:
            set_info(str(data["error"]), True)
            return

        generated_stl_blob = Blob.new([to_js(binascii.a2b_base64(data["stl"]))], {type: "model/stl"})  # type: ignore
        generated_step_blob = Blob.new([to_js(binascii.a2b_base64(data["step"]))], {type: "model/step"})  # type: ignore

        roughness = data.get("roughness", 0.5)
        metalness = data.get("metalness", 0.95)
        color = data.get("color", 0xE3BD7A)
        description = data.get("description", "There is no key...")

        stl_url = URL.createObjectURL(generated_stl_blob)
        await model_view.loadObject(stl_url, roughness, metalness, color)

        stl_blob = generated_stl_blob
        step_blob = generated_step_blob
        model_description.html = str(description)
        set_info("")
        update_download_availability()
    except Exception as error:
        set_info(f"Generation failed: {error}", True)
    finally:
        try:
            if stl_url is not None:
                URL.revokeObjectURL(stl_url)
        finally:
            generation_in_progress = False
            set_model_overlay_text()
            update_generation_availability()
            update_download_availability()


# Model downloads
def save_shared(blob, extension: str):
    url = URL.createObjectURL(blob)
    hidden_link = document.createElement("a")  # type: ignore
    hidden_link.setAttribute("download", html.unescape(f"{model_description.html}.{extension}"))
    hidden_link.setAttribute("href", url)
    hidden_link.click()
    URL.revokeObjectURL(url)


@when("click", "#save-stl")
def save_as_stl():
    if stl_blob is None:
        return

    save_shared(stl_blob, "stl")


@when("click", "#save-step")
def save_as_step():
    if step_blob is None:
        return

    save_shared(step_blob, "step")


# Sharing and notifications
@when("click", "#copy-link")
async def create_share_link():
    base_url = URL.new(window.location.origin + window.location.pathname)

    current_tab = get_selected_tab()
    base_url.searchParams["tab"] = current_tab[1]

    if share_settings.checked:
        settings = current_tab[0].get_query_params()
        base_url.searchParams.update(settings)
    if share_generate.checked:
        base_url.searchParams["generate"] = "true"

    try:
        await navigator.clipboard.writeText(str(base_url))
    except Exception:
        await show_toast("Could not copy link. Check clipboard permissions and try again.", False)
        return

    share_dialog.close()
    await show_toast("Share link copied to the clipboard.", True)


async def show_toast(message: str, success: bool):
    global toast_version
    toast_version += 1
    current_version = toast_version

    if toast.matches(":popover-open"):
        toast.hide_popover()

    state_class: str = "toast-success" if success else "toast-failure"
    icon_class: str = "fa-circle-check" if success else "fa-circle-exclamation"
    toast.html = f'<div class="toast-message {state_class}"><i class="fa-solid {icon_class}" aria-hidden="true"></i><span>{message}</span></div>'
    toast.show_popover()

    await asyncio.sleep(4)
    if toast_version == current_version and toast.matches(":popover-open"):  # type: ignore
        toast.hide_popover()  # type: ignore
