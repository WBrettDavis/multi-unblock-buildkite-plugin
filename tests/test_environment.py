import os
from unittest import TestCase
from unittest.mock import patch
from src.environment import Environment, EnvironmentValidationError


def mockenv(**envvars):
    return patch.dict(os.environ, envvars)


class EnvironmentTest(TestCase):
    @mockenv(
        BUILDKITE_API_TOKEN="test",
    )
    def test_validate_happy_path(self) -> None:
        # arrange
        env = Environment()

        # act
        env.validate()

        # assert
        assert True  # Asserts that an exception wasn't raised

    @mockenv(
        BUILDKITE_API_TOKEN="",
    )
    def test_validate_api_token_missing_fails(self) -> None:
        # arrange
        env = Environment()

        # act/assert
        self.assertRaises(EnvironmentValidationError, env.validate)


