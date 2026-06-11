from pyscript import web, when
from pyscript.ffi import to_js
from js import Blob, URL
from pyscript.js_modules import model_view  # type: ignore

from realkey import tab, web_core, web_main

follower_select = web_core.SelectElement(web.page["follower-select"])
follower_length = web_core.LengthInputElement(web.page["follower-length"])
follower_diameter = web_core.LengthInputElement(web.page["follower-diameter"])
follower_top_select = web_core.SelectElement(web.page["follower-top-select"])
follower_top_div = web_core.Element(web.page["follower-top-div"])
follower_bottom_select = web_core.SelectElement(web.page["follower-bottom-select"])
follower_bottom_div = web_core.Element(web.page["follower-bottom-div"])

class FollowerTab(tab.Tab):
    def __init__(self, button: web_core.Element, tab: web_core.Element) -> None:
        super().__init__(button, tab)
       
    def load_from_params(self, query_params):
        pass

    async def generate(self, bg_worker) -> dict[str, str]:
        raise NotImplementedError

