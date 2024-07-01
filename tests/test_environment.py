import os
from unittest import TestCase
from unittest.mock import patch
from src.environment import Environment, EnvironmentValidationError


def mockenv(**envvars):
    return patch.dict(os.environ, envvars)


class EnvironmentTest(TestCase):
    @mockenv(
        BUILDKITE_PLUGIN_MULTI_APPROVAL_COMMAND="",
        BUILDKITE_PLUGIN_MULTI_APPROVAL_SUCCESS_KEY="test",
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
        BUILDKITE_PLUGIN_MULTI_APPROVAL_COMMAND="",
        BUILDKITE_PLUGIN_MULTI_APPROVAL_SUCCESS_KEY="test",
        BUILDKITE_API_TOKEN="",
    )
    def test_validate_api_token_missing_fails(self) -> None:
        # arrange
        env = Environment()

        # act/assert
        self.assertRaises(EnvironmentValidationError, env.validate)

    @mockenv(
        BUILDKITE_PLUGIN_MULTI_APPROVAL_COMMAND="",
        BUILDKITE_PLUGIN_MULTI_APPROVAL_SUCCESS_KEY="",
        BUILDKITE_API_TOKEN="test",
    )
    def test_validate_success_key_missing_fails(self) -> None:
        # arrange
        env = Environment()

        # act/assert
        self.assertRaises(EnvironmentValidationError, env.validate)

    @mockenv(
        BUILDKITE_PLUGIN_MULTI_APPROVAL_COMMAND="success",
        BUILDKITE_PLUGIN_MULTI_APPROVAL_SUCCESS_KEY="",
        BUILDKITE_API_TOKEN="test",
    )
    def test_validate_success_key_missing_ok_on_success(self) -> None:
        # arrange
        env = Environment()

        # act
        env.validate()

        # assert
        assert True  # Asserts that an exception wasn't raised
