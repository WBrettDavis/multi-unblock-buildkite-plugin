import os
import typing as t

PLUGIN_ENV_VAR_PREFIX = "BUILDKITE_PLUGIN_MULTI_UNBLOCK"


class EnvironmentValidationError(Exception):
    """Throws when an environment configuration validation error occurs"""


class Environment:
    def _get_config_property_env_var(self, property_name: str) -> str:
        formatted_property_name = property_name.upper().replace("-", "_")
        return f"{PLUGIN_ENV_VAR_PREFIX}_{formatted_property_name}"

    def _get_plugin_config_str(
        self, property_name: str, default: t.Optional[str] = None
    ) -> t.Optional[str]:
        property_env_var = self._get_config_property_env_var(property_name)
        property_value = os.getenv(property_env_var, default)
        return property_value

    def _get_plugin_config_int(
        self, property_name: str, default: t.Optional[int] = None
    ) -> int:
        property_env_var = self._get_config_property_env_var(property_name)
        property_raw_value = os.getenv(property_env_var, None)
        if property_raw_value is None:
            return default
        return int(property_raw_value)

    def _get_plugin_config_bool(self, property_name: str) -> bool:
        property_env_var = self._get_config_property_env_var(property_name)
        property_value = os.getenv(property_env_var)
        return (
            True
            if property_value and property_value.lower() in ["true", "yes"]
            else False
        )

    def _get_plugin_config_list(self, property_name: str) -> t.List[str]:
        property_env_var = self._get_config_property_env_var(property_name)
        property_values = []
        array_index = 0
        while True:
            index_value = os.getenv(f"{property_env_var}_{array_index}")
            if not index_value:
                break
            property_values.append(index_value)
            array_index += 1
        return property_values

    @property
    def org(self) -> str:
        return os.getenv("BUILDKITE_ORGANIZATION_SLUG")

    @property
    def pipeline_slug(self) -> int:
        return os.getenv("BUILDKITE_PIPELINE_SLUG")

    @property
    def build_number(self) -> int:
        return int(os.getenv("BUILDKITE_BUILD_NUMBER"))

    @property
    def api_token_name(self) -> str:
        api_token_name = self._get_plugin_config_str("api-token")
        if not api_token_name:
            api_token_name = "BUILDKITE_API_TOKEN"
        return api_token_name

    @property
    def api_token(self) -> str:
        return os.getenv(self.api_token_name)

    @property
    def block_step_pattern(self) -> t.Optional[str]:
        return self._get_plugin_config_str("block-step-pattern")

    @property
    def block_steps(self) -> t.List[str]:
        return self._get_plugin_config_list("block-steps")

    @property
    def override_step_key(self) -> t.Optional[str]:
        return self._get_plugin_config_str("override-step-key")

    @property
    def timeout_seconds(self) -> t.Optional[int]:
        return self._get_plugin_config_int("timeout-seconds", None)

    def validate(self) -> None:
        if not self.api_token:
            raise EnvironmentValidationError(
                "Buildkite API token not set. See Plugin README for details."
            )
