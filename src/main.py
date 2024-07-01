import json
import os
import typing as t
from src.models import Pipeline, PluginStep, ApprovalStep
from src.buildkite_agent import BuildkiteAgent
from src.buildkite_api import BuildkiteApi, BuildkiteUser
from src.environment import Environment

SELF_PLUGIN_NAME = "affirm/multi-approval"
APPROVAL_VALIDATION_FAILED_EXIT_CODE = 99
FAILED_EMOJI = ":negative_squared_cross_mark:"
SUCCESS_EMOJI = ":white_check_mark:"


class MultiUnblockPlugin:
    def __init__(
        self, env: Environment, api: BuildkiteApi, agent: BuildkiteAgent
    ) -> None:
        self.env = env
        self.api = api
        self.agent = agent

    def _get_self_plugin(self) -> str:
        bk_plugins = os.getenv("BUILDKITE_PLUGINS")
        if bk_plugins:
            plugins_list = json.loads(bk_plugins)
            for plugin in plugins_list:
                for key, _ in plugin.items():
                    if SELF_PLUGIN_NAME in key:
                        return key

    def _get_additional_plugins(self) -> t.List[dict]:
        bk_plugins = os.getenv("BUILDKITE_PLUGINS")
        if bk_plugins:
            plugins_list = json.loads(bk_plugins)
            addl_plugins = []
            for plugin in plugins_list:
                for key, value in plugin.items():
                    if SELF_PLUGIN_NAME not in key:
                        addl_plugins.append({key: value})
            return addl_plugins

    def generate_approval_step(self) -> None:
        attempt = self.env.attempt + 1
        print("--- Generating Approval Step")
        print(f"Attempt Count: {self.env.attempt}")
        steps = []
        approval_step = ApprovalStep(
            key=f"{self.env.success_key}-block-{attempt}",
            label=f":key: Approval Required",
            prompt=self._format_approvers_list(),
        )
        verify_step = PluginStep(
            key=f"{self.env.success_key}-verify-{attempt}",
            label=":mag: Validate approver",
            plugin_version=self._get_self_plugin(),
            api_token_name=self.env.api_token_name,
            command="verify",
            self_approval=self.env.self_approval,
            approval_step_key=approval_step.key,
            success_key=self.env.success_key,
            users=self.env.users,
            teams=self.env.teams,
            attempt=attempt,
            additional_plugins=self._get_additional_plugins(),
            soft_fail_exit_code=APPROVAL_VALIDATION_FAILED_EXIT_CODE,
            metadata_key=self.env.metadata_key,
        )
        steps.extend([approval_step, verify_step])
        pipeline = Pipeline(steps=[approval_step, verify_step])
        self.agent.pipeline_upload(pipeline.to_dict())

    def main(self) -> None:
        jobs = self.api.get_unblockable_jobs_in_build(env.pipeline_slug, env.build_number)
        print(f"Found {len(jobs)} unblockable jobs")
        for j in jobs:
            self.api.unblock_job(env.pipeline_slug, env.build_number, j.id)


if __name__ == "__main__":
    env = Environment()
    env.validate()
    api = BuildkiteApi(env.api_token, env.org)
    agent = BuildkiteAgent()
    plugin = MultiUnblockPlugin(env, api, agent)
    plugin.main()
