from unittest.mock import patch, Mock
from src.main import MultiUnblockPlugin
from src.buildkite_agent import BuildkiteAgent
from src.environment import Environment
from src.buildkite_api import BuildkiteApi, BuildkiteJob


def test_unblock_happy_path() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.api_token = "test-123"
    env_mock.pipeline_slug = "test-pipeline-slug"
    env_mock.build_number = 123
    agent_mock = Mock(spec=BuildkiteAgent)
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_unblockable_jobs_in_build.return_value = [BuildkiteJob(id="test", step_key="test", unblockable=True, state="unknown")]
    plugin = MultiUnblockPlugin(env_mock, api_mock, agent_mock)

    # act
    plugin.main()

    # assert
    assert True
