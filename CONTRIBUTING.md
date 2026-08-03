# How to Contribute

## Architecture

The browser application is split into lightweight foreground code and a CAD worker:

- [main.py](main.py) starts the foreground PyScript runtime. It mocks the build123d surface needed to import metadata without loading the CAD engine.
- [web_main.py](src/realkey/web_main.py) handles all the foreground logic including tabs, generation, downloading, and sharing
- [worker.py](worker.py) installs build123d and its browser dependencies, generates geometry, and exports STL and STEP data.
- [model_view.js](model_view.js) loads STL data into Three.js and manages model fitting, resizing, materials, lighting, and resource disposal.

The foreground interface remains usable while the worker loads. Geometry operations belong in `blank()`, `key()`, follower generation, or worker-side helpers; metadata and validation methods must remain safe to import in the lightweight foreground runtime.

`Key` and `FollowerEnd` subclasses register themselves in typed class registries. The UI builds its available options from these registries.

## Development Setup

realkey requires Python 3.14.

```console
python -m venv .venv
```

Activate the virtual environment, then install the development dependencies and run the tests:

```console
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```
Use `ocp_vscode` to inspect geometry while developing in VS Code. Key modules contain optional `__main__` blocks that can be adapted for local visualization and export.

## Adding a Key

### Implement the key class

Create a module under `src/realkey/` and define a class extending [Key](src/realkey/key.py). Implement the following class methods:

- **`tag()`** returns a unique internal snake-case identifier, such as `miwa_sr`.
- **`display_name()`** returns the name shown in the interface.
- **`profiles()`** returns grouped profile options in the form `{"Group": {"tag": "Display name"}}`. Use an empty outer key for ungrouped options.
- **`keyways()`** returns grouped keyway options using the same structure.
- **`basic_bitting_definition()`** returns concise HTML explaining cut count, order, depth range, and an example.
- **`advanced_bitting_definition()`** returns detailed HTML for the popover, or `None` when no advanced information is needed.
- **`validate_bitting()`** rejects invalid cut counts, characters, track structure, and depth ranges with a useful exception message.
- **`blank()`** returns a valid, non-empty build123d `Part` for the requested profile and keyway.
- **`key()`** validates the bitting, builds the blank, applies the cuts, and returns a valid build123d `Part`.

Keep validation and metadata independent of heavy CAD behavior. The foreground calls them before the worker has loaded build123d.

### Add geometry resources

Place runtime assets under:

```text
src/realkey/resources/<family>/
```

Load resource files through [resource_fetcher.py](src/realkey/resource_fetcher.py):

```python
resource_path = resource_fetcher.fetch_resource("resources/Example/Blank.svg")
if resource_path is None:
    raise ValueError("Unable to load Example SVG")
geometry = import_svg(resource_path)
```

Do not open repository-relative resource names directly. `fetch_resource()` resolves installed package data for native Python and lazily downloads the same asset in the browser worker. Browser-only image URLs use the static `src/realkey/resources/...` path.

The package-data patterns in `pyproject.toml` include files directly inside `resources/` and one family directory below it. Update those patterns if a deeper directory structure is introduced.

### Register the module

Import the new module in all three locations:

- [tab_key.py](src/realkey/tab_key.py), so the foreground registry contains it.
- [worker.py](worker.py), so the worker registry contains it.
- [test_geometry.py](tests/test_geometry.py), so automated geometry coverage contains it.

Also add the Python module to the `files` mapping in [config.json](config.json), which makes it available to PyScript.

### Add or update tests

The geometry suite checks:

- representative key blank/profile/keyway combinations;
- every predefined follower configuration;
- every top and bottom follower-end pairing; and
- resource-backed generation from outside the repository working directory.

Add focused tests for parsing, validation, or geometry behavior that is not covered by these registry-driven smoke tests. Tests should assert that generated parts are valid, contain one solid, and have positive volume.

Run the suite before submitting changes:

```console
python -m unittest discover -s tests -v
```

## Adding a Follower End

Create a `FollowerEnd` subclass in [follower.py](src/realkey/follower.py) and implement its tag, display name, configuration schema, generated length, and geometry generation.

Configuration names should end in `_depth`, `_width`, or `_wall_thickness` where applicable so the combination tests can create representative values. If a new type is added, please add it to the combination tests. Validate constraints such as positive dimensions, wall thickness relative to radius, and the combined end length before invoking low-level CAD operations.

Add useful presets to `FOLLOWER_DEFINITIONS` when the dimensions represent a possibly reusable follower.
