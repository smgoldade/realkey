import micropip
from pyscript import display, workers

# Bootstrap load in build123d
async def bootstrap(ocp_index = "https://yeicor.github.io/OCP.wasm"):
    # Prioritize the OCP.wasm package repository so that wasm-specific packages are preferred.
    micropip.set_index_urls([ocp_index, "https://pypi.org/simple"])

    # Install the required packages.
    await micropip.install(["ipython == 9.10.0", "build123d"])

# Kick off loading worker

# Load the boot strap
display("Bootstrapping build123d...", target = "status", append = False)
result = await bootstrap()
display("Waiting for background worker...", target = "status", append = False)
keygen = await workers["keygen"]
display("Loaded!", target = "status", append = False)

# Jump into realkey
from realkey import realkey
realkey.main(keygen)