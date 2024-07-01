#!/usr/bin/env bats

load "$BATS_PLUGIN_PATH/load.bash"

# Uncomment the following line to debug stub failures
# export BUILDKITE_AGENT_STUB_DEBUG=/dev/tty

@test "Uploads approval steps" {
  export BUILDKITE_PLUGIN_MULTI_APPROVAL_APPROVAL_TYPE="user"
  export BUILDKITE_PLUGIN_MULTI_APPROVAL_USER_EMAIL="test@test.com"

  stub python3 'echo "Generating approval steps"'

  run "$PWD/hooks/command"

  assert_success
  assert_output --partial "Generating approval steps"

  unstub python3
}