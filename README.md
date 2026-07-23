# [realkey](https://smgoldade.github.io/realkey)

[![Tests](https://github.com/smgoldade/realkey/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/smgoldade/realkey/actions/workflows/tests.yml)

realkey is a Python project designed to generate keys and other locksport tools. It is available as an interactive browser application and as a Python library built on [build123d](https://github.com/gumyr/build123d).

## Features

- Generate blank or cut keys.
- Generate plug followers using a library of possible follower ends.
- The browser application shows a preview of the generated model.
- Models can be downloaded as STL or STEP files directly.
- Share generated keys and followers with others via generatable links
- Generation is local to the browser when used as a browser application

## Python Library

realkey is built on Python. To install the current checkout:

```console
python -m pip install .
```

Key implementations return build123d `Part` objects:

```python
from realkey.paclock import PR1

blank = PR1.blank("pr1", "pr1")
cut_key = PR1.key("pro", "pr1", "6212121")
```

## Key Model

The conceptual idea behind the key taxonomy is as follows:
- A singular key is defined by a bitting, keyway, profile, and type.
- **Bitting** is a unique code that links a key to a lock, typically a numeric code specifying the cuts to be made. *E.g. "145762"*
- **Keyway** defines the shape of the portion of the key that enters the lock. Some locks may come with a variety of different keyways. *E.g. C*
- **Profile** defines the shape of the entire key from a profile view. This commonly is different between different pin count versions of the same lock type. *E.g. 6-pin*
- **Type** defines the specific lock or lock family that the key works for. *E.g. Schlage Classic*

## Repository Layout

- `src/realkey/` contains key, follower, geometry, resource, and web-interface modules.
- `src/realkey/resources/` contains packaged SVG, STEP, STL, and image assets.
- `main.py` initializes the lightweight foreground PyScript interface.
- `worker.py` installs the CAD runtime and performs geometry generation in a background worker.
- `model_view.js` owns the Three.js preview, camera fitting, lighting, and model disposal.
- `tests/` contains geometry and packaged-resource regression tests.
- `.github/workflows/tests.yml` runs the test suite on Python 3.13.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and extension guidance.

## Inspiration

Several projects inspired realkey:
- [Eric Van Albert's keygen](https://github.com/ervanalb/keygen)
- [Reinder's 3D Printing Keys](https://github.com/reinder-s/3d-printing-keys/tree/main)
- [Christian Holler's AutoKey3D](https://github.com/choller/autokey3d)