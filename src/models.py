import typing as t


class JsonSerializable:
    def to_dict(self) -> dict:
        pass


class PipelineStep(JsonSerializable):
    def to_dict(self) -> dict:
        pass


class Pipeline(JsonSerializable):
    def __init__(self, steps: t.List[PipelineStep]) -> None:
        self.steps = steps

    def to_dict(self) -> dict:
        return {"steps": [step.to_dict() for step in self.steps]}


class ApprovalStep(PipelineStep):
    def __init__(self, key: str, label: str, prompt: str) -> None:
        self.key = key
        self.label = label
        self.prompt = prompt

    def to_dict(self) -> dict:
        return {"key": self.key, "block": self.label, "prompt": self.prompt}


class PluginStep(PipelineStep):
    def __init__(
        self,
        key: str,
        label: str,
        plugin_version: str,
        api_token_name: str,
        command: t.Optional[str] = None,
        self_approval: t.Optional[bool] = None,
        approval_step_key: t.Optional[str] = None,
        users: t.Optional[t.Set[str]] = None,
        teams: t.Optional[t.Set[str]] = None,
        success_key: t.Optional[str] = None,
        attempt: t.Optional[int] = None,
        additional_plugins: t.Optional[t.List[dict]] = None,
        soft_fail_exit_code: t.Optional[int] = None,
        metadata_key: t.Optional[str] = None,
    ) -> None:
        self.key = key
        self.label = label
        self.plugin_version = plugin_version
        self.additional_plugins = additional_plugins
        if not additional_plugins:
            additional_plugins = []
        multi_approval_plugin_config = {
            "self-approval": self_approval,
            "approval-step-key": approval_step_key,
            "command": command,
            "success-key": success_key,
            "attempt": attempt,
            "teams": list(teams) if teams else None,
            "users": list(users) if users else None,
            "api-token": api_token_name,
            "metadata-key": metadata_key,
        }
        empty_keys = set()
        for key in multi_approval_plugin_config:
            if not multi_approval_plugin_config[key]:
                empty_keys.add(key)
        for key in empty_keys:
            del multi_approval_plugin_config[key]
        multi_approval_plugin = {f"{self.plugin_version}": multi_approval_plugin_config}
        self.plugins = [*additional_plugins, multi_approval_plugin]
        self.soft_fail_exit_code = soft_fail_exit_code
        self.depends_on = [approval_step_key] if approval_step_key else []

    def to_dict(self) -> dict:
        step_dictionary = {
            "label": self.label,
            "plugins": self.plugins,
            "key": self.key,
        }
        if self.depends_on:
            step_dictionary["depends_on"] = self.depends_on
        if self.soft_fail_exit_code:
            step_dictionary["soft_fail"] = [{"exit_status": self.soft_fail_exit_code}]
        return step_dictionary
