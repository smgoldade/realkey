"""Geometry smoke tests for keys and followers."""

import unittest
from collections.abc import Iterator

from build123d import Part

# Import every key implementation so Key's subclass registry is populated.
from realkey import (  # noqa: F401
    assa,
    dom,
    miwa,
    opnus,
    paclock,
    sargentandgreenleaf,
    schlage,
    vsr,
)
from realkey.follower import (
    FOLLOWER_DEFINITIONS,
    Follower,
    FollowerConfigData,
    FollowerEnd,
)
from realkey.key import Key


def _flatten_groups(groups: dict[str, dict[str, str]]) -> list[str]:
    """Return the internal values from a grouped select-options mapping."""
    return [value for group in groups.values() for value in group]


def blank_combinations() -> Iterator[tuple[type[Key], str, str]]:
    """Yield one representative profile with every keyway for each key type.

    Profiles within a key type generally change the bow or pin-count geometry,
    while keyways exercise the resource-backed profile subtraction. Testing the
    first profile against every keyway keeps this smoke test comprehensive for
    keyway resources without expanding to the full Cartesian product.
    """
    for key_type in Key._list.values():
        profiles = _flatten_groups(key_type.profiles())
        keyways = _flatten_groups(key_type.keyways())

        if not profiles:
            raise AssertionError(f"{key_type.__name__} does not define a profile")
        if not keyways:
            raise AssertionError(f"{key_type.__name__} does not define a keyway")

        profile = profiles[0]
        for keyway in keyways:
            yield key_type, profile, keyway


def follower_combinations() -> Iterator[tuple[str, FollowerConfigData]]:
    """Yield every predefined follower configuration except the custom entry."""
    for name, config in FOLLOWER_DEFINITIONS.items():
        if config is not None:
            yield name, config


def _representative_end_config(end_type: type[FollowerEnd]) -> dict[str, float]:
    """Build valid representative dimensions from a follower end's schema."""
    config: dict[str, float] = {}
    for field in end_type.config():
        if field.endswith("_depth"):
            config[field] = 5.0
        elif field.endswith("_wall_thickness"):
            config[field] = 1.0
        elif field.endswith("_width"):
            config[field] = 3.0
        else:
            raise AssertionError(f'No representative value is defined for follower field "{field}"')

    if config:
        config["rotation"] = 0.0
    return config


def follower_end_combinations() -> Iterator[
    tuple[str, dict[str, float], str, dict[str, float]]
]:
    """Yield every registered follower end as both the top and bottom end."""
    for top_tag, top_type in FollowerEnd._list.items():
        for bottom_tag, bottom_type in FollowerEnd._list.items():
            yield (
                top_tag,
                _representative_end_config(top_type),
                bottom_tag,
                _representative_end_config(bottom_type),
            )


class GeometryTests(unittest.TestCase):
    def assert_valid_solid(self, part: Part, description: str):
        self.assertTrue(part.is_valid, f"{description} is not a valid BRep")
        self.assertEqual(len(part.solids()), 1, f"{description} is not a single solid")
        self.assertGreater(part.volume, 0, f"{description} has no volume")

    def test_representative_blank_combinations_are_valid_solids(self):
        for key_type, profile, keyway in blank_combinations():
            with self.subTest(key=key_type.tag(), profile=profile, keyway=keyway):
                blank = key_type.blank(profile, keyway)
                self.assert_valid_solid(blank, "generated blank")

    def test_predefined_follower_combinations_are_valid_solids(self):
        for name, config in follower_combinations():
            with self.subTest(follower=name, top=config.top_tag, bottom=config.bottom_tag):
                generated_follower = Follower.generate(config)
                self.assert_valid_solid(generated_follower, "generated follower")

    def test_all_follower_end_combinations_are_valid_solids(self):
        for top_tag, top_config, bottom_tag, bottom_config in follower_end_combinations():
            with self.subTest(top=top_tag, bottom=bottom_tag):
                config = FollowerConfigData(
                    70.0,
                    12.0,
                    top_tag,
                    top_config,
                    bottom_tag,
                    bottom_config,
                )
                generated_follower = Follower.generate(config)
                self.assert_valid_solid(generated_follower, "generated follower")


if __name__ == "__main__":
    unittest.main()
