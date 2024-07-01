from unittest.mock import patch, Mock
from src.main import MultiApprovalPlugin, APPROVAL_VALIDATION_FAILED_EXIT_CODE
from src.buildkite_agent import BuildkiteAgent
from src.environment import Environment
from src.buildkite_api import BuildkiteApi, BuildkiteUser


def test_generate_creator_approval_uploads_steps() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = None
    env_mock.attempt = 0
    env_mock.self_approval = True
    env_mock.users = set()
    env_mock.teams = set()
    env_mock.build_creator_email = "test@test.com"
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    plugin.main()

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_generate_user_approval_uploads_steps() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = None
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set(["test@test.com"])
    env_mock.teams = set()
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    plugin.main()

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_generate_team_approval_uploads_steps() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = None
    env_mock.attempt = 0
    env_mock.self_approval = True
    env_mock.teams = set(["prod-deployers"])
    env_mock.users = set()
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    plugin.main()

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_user_success() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = True
    env_mock.users = set(["test@test.com"])
    env_mock.teams = set()
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == 0

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_creator_success() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = True
    env_mock.users = set()
    env_mock.teams = set()
    env_mock.build_creator_email = "test@test.com"
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == 0

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_not_creator_fails() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set(["test@test.com"])
    env_mock.teams = set()
    env_mock.build_creator_email = "test@test.com"
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == APPROVAL_VALIDATION_FAILED_EXIT_CODE

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_sets_approver_metadata() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.users = set(["test@test.com"])
    env_mock.self_approval = False
    env_mock.teams = set()
    env_mock.metadata_key = "approver"
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.set_metadata = Mock()
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    mock_bk_user = BuildkiteUser(id="123", name="Test", email="test@test.com")
    api_mock.get_step_approver.return_value = mock_bk_user
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == 0

    # assert
    agent_mock.set_metadata.assert_called_once()


def test_command_verify_user_fail() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set(["test@test.com"])
    env_mock.teams = set()
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="not-test@test.com"
    )
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == APPROVAL_VALIDATION_FAILED_EXIT_CODE

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_team_success() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set()
    env_mock.teams = set(["prod-deployers"])
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    api_mock.get_user_teams = Mock()
    api_mock.get_user_teams.return_value = set(["prod-deployers"])
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == 0

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_multi_team_success() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set()
    env_mock.teams = set(["prod-deployers", "prod-admins"])
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    api_mock.get_user_teams = Mock()
    api_mock.get_user_teams.return_value = set(["prod-admins"])
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == 0

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_verify_team_fail() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "verify"
    env_mock.attempt = 0
    env_mock.self_approval = False
    env_mock.users = set()
    env_mock.teams = set(["prod-deployers"])
    agent_mock = Mock(spec=BuildkiteAgent)
    agent_mock.pipeline_upload = Mock()
    api_mock = Mock(spec=BuildkiteApi)
    api_mock.get_step_approver = Mock()
    api_mock.get_step_approver.return_value = BuildkiteUser(
        id="123", name="Test", email="test@test.com"
    )
    api_mock.get_user_teams = Mock()
    api_mock.get_user_teams.return_value = set(["not-prod-deployers"])
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    except SystemExit as e:
        assert e.code == APPROVAL_VALIDATION_FAILED_EXIT_CODE

    # assert
    agent_mock.pipeline_upload.assert_called_once()


def test_command_success_exit_0() -> None:
    # arrange
    env_mock = Mock(spec=Environment)
    env_mock.command = "success"
    agent_mock = Mock(spec=BuildkiteAgent)
    api_mock = Mock(spec=BuildkiteApi)
    plugin = MultiApprovalPlugin(env_mock, api_mock, agent_mock)

    # act
    try:
        plugin.main()
    # assert
    except SystemExit as e:
        assert e.code == 0
