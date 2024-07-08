import logging
import subprocess
import typing as t

logging.basicConfig()
logger = logging.getLogger(__name__)

class BuildkiteAgent:
    def _buildkite_agent(self, args: t.List[str]) -> str:
        agent_command = ["buildkite-agent", *args]
        logger.debug(f"Running buildkite-agent command: {' '.join(agent_command)}")
        completed_process = subprocess.run(
            agent_command,
            timeout=600,
            text=True,
            capture_output=True,
        )
        # If return code is not 0, buildkite-agent command returned an error
        if completed_process.returncode != 0:
            logger.debug(f"The buildkite-agent command failed.")
            logger.debug(f"Return Code: {completed_process.returncode}")
            logger.debug(f"STDOUT: \n{completed_process.stdout}")
            logger.debug(f"STDERR: \n{completed_process.stderr}")
            logger.error("buildkite-agent command failed")
            raise Exception("The buildkite-agent command failed.")
        return completed_process.stdout

    def update_self_step_label(self, label: str) -> None:
        logger.debug(f"Updating self step label to: {label}")
        self._buildkite_agent(["step", "update", "label", label])

    def get_self_step_label(self) -> str:
        logger.debug("Getting self step label")
        return self._buildkite_agent(["step", "get", "label"])

    def get_step_state(self, step_key: str) -> str:
        logger.debug(f"Getting step state for step: {step_key}")
        step_state = self._buildkite_agent(["step", "get", "state", "--step", step_key])
        return step_state
