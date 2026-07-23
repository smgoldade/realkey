import sys

from js import URL
import micropip  # type: ignore
from pyscript import display, window, workers

# Kick off key generating worker
display("Loading interface...", target="status", append=False)
keygen_loading = workers["keygen"]
await micropip.install(["typing-extensions"])


# Mock build123d
class Empty[T]:
    pass


bogus123d = Empty()
sys.modules["build123d"] = bogus123d

# Mock features of build123d adhering to the ideas:
# - Any BRep or geometry generation should fail, we should not be doing that on the light web front-end!
# - Anything else is fine, and we should have reasonable implementations
bogus123d.MM = 1
bogus123d.IN = 25.4
bogus123d.THOU = 0.0254
bogus123d.Face = Empty
bogus123d.Part = Empty
bogus123d.ShapeList = Empty
bogus123d.Sketch = Empty
bogus123d.Vector = Empty
bogus123d.VectorLike = Empty
bogus123d.Wire = Empty

# Jump into realkey
from realkey import web_main

await web_main.main()

print("[FG] Waiting for background install")
try:
    keygen = await keygen_loading
    base_url = URL.new(".", window.location.href).href.rstrip("/")
    await keygen.set_base_url(base_url)
except Exception as error:
    print(f"[FG] Background worker failed to load: {error}")
    web_main.background_worker_failed()
else:
    print("[FG] Background worker loaded")
    await web_main.background_worker_loaded(keygen)
