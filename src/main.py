import typing as t
from src.buildkite_agent import BuildkiteAgent
from src.buildkite_api import BuildkiteApi
from src.environment import Environment

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

    def main(self) -> None:
        jobs = self.api.get_unblockable_jobs_in_build(
            self.env.pipeline_slug, self.env.build_number
        )
        print(f"Found {len(jobs)} unblockable jobs")
        for job in jobs:
            self.api.unblock_job(job)


if __name__ == "__main__":
    env = Environment()
    env.validate()
    api = BuildkiteApi(env.api_token, env.org)
    agent = BuildkiteAgent()
    plugin = MultiUnblockPlugin(env, api, agent)
    plugin.main()
