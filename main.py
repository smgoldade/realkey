import micropip, asyncio, os
from pyscript import display

# Bootstrap load in build123d
async def bootstrap(ocp_index = "https://yeicor.github.io/OCP.wasm"):
    # Prioritize the OCP.wasm package repository so that wasm-specific packages are preferred.
    micropip.set_index_urls([ocp_index, "https://pypi.org/simple"])

    # Install the required packages.
    micropip.add_mock_package("psutil", "5.9")
    await micropip.install(["build123d"])


# Load the boot strap
display("Bootstrapping build123d...", target="status", append=False)
result = await bootstrap()
display("Loaded!", target="status", append=False)

# Jump into realkey
from realkey import realkey
realkey.main()