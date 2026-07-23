"""Tests for loading geometry resources."""

import os
import tempfile
import unittest
from pathlib import Path

from realkey import resource_fetcher
from realkey.paclock import PR1


class ResourceTests(unittest.TestCase):
    def test_resource_backed_blank_is_independent_of_working_directory(self):
        original_working_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                resource_path = resource_fetcher.fetch_resource("resources/Paclock/PR1.svg")
                blank = PR1.blank("pr1", "pr1")
            finally:
                os.chdir(original_working_directory)

        self.assertIsNotNone(resource_path)
        assert resource_path is not None
        self.assertTrue(Path(resource_path).is_relative_to(Path(resource_fetcher.__file__).parent))
        self.assertTrue(blank.is_valid)
        self.assertEqual(len(blank.solids()), 1)
        self.assertGreater(blank.volume, 0)


if __name__ == "__main__":
    unittest.main()
