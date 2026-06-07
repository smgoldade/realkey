from typing import Iterable

from pyscript import web


class Element:
    def __init__(self, web_element: web.ElementCollection) -> None:
        self._web_element = web_element

    @property
    def enabled(self) -> bool:
        return not self._web_element.disabled

    @enabled.setter
    def enabled(self, value: bool):
        if value:
            self._web_element.removeAttribute("disabled")  # type: ignore
        else:
            self._web_element.disabled = True

    @property
    def html(self) -> str:
        return str(self._web_element.innerHTML)

    @html.setter
    def html(self, value: str):
        self._web_element.innerHTML = value

    @property
    def hidden(self) -> bool:
        return "hide" in self._web_element.classes
    
    @hidden.setter
    def hidden(self, value: bool):
        if value:
            if not "hide" in self._web_element.classes:
                self._web_element.classes.add("hide")
        else:
            self._web_element.classes.discard("hide") # type: ignore


class ValueElement(Element):
    def __init__(self, web_element: web.ElementCollection) -> None:
        super().__init__(web_element)

    @property
    def value(self) -> str:
        return str(self._web_element.value)

    @value.setter
    def value(self, v: str):
        self._web_element.value = v


class OptionElement(ValueElement):
    def __init__(self, web_element: web.ElementCollection) -> None:
        super().__init__(web_element)

    @property
    def selected(self) -> bool:
        if hasattr(self._web_element, "selected"):
            return bool(self._web_element.selected)
        return False

    @selected.setter
    def selected(self, value: bool):
        if value:
            self._web_element.selected = True
        else:
            self._web_element.removeAttribute("selected")  # type: ignore

    def __str__(self):
        return f"{self._web_element.value} : {self._web_element.innerHTML} : {self.selected}"


class OptionElementList(list[OptionElement]):
    def __init__(self, iterable: Iterable[OptionElement]) -> None:
        super().__init__(iterable)

    @property
    def selected(self):
        for option in self:
            if option.selected:
                return option
        return self[0]
    
    def __str__(self):
        strs = [str(e) for e in self]
        return f"[{",".join(strs)}]"

class SelectElement(Element):
    def __init__(self, web_element: web.ElementCollection) -> None:
        super().__init__(web_element)

    def populate(self, null_string: str, options_dict: dict[str, dict[str, str]]):
        self._web_element.replaceChildren()
        if len(null_string) > 0:
            self._web_element.options.add(value="null", html=null_string)  # type: ignore
        for optgroup, options in options_dict.items():
            if len(optgroup) > 0:
                group = web.optgroup(label=optgroup)
                self._web_element.append(group)
                for value,html in options.items():
                    opt = web.option(innerHTML=html, value=value)
                    group.append(opt)  # type: ignore
            else:
                for value,html in options.items():
                    self._web_element.options.add(value=value, html=html)  # type: ignore           

    @property
    def options(self) -> OptionElementList:
        options = OptionElementList([])

        for child in self._web_element.children:
            if "optgroup" == child.get_tag_name():
                for child in child.children:
                    options.append(OptionElement(child))
            else:
                options.append(OptionElement(child))
        return options

    @property
    def selected_value(self) -> str:
        return self.options.selected.value

    @property
    def selected_html(self) -> str:
        return self.options.selected.html
