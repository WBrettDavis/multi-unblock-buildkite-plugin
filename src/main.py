import time
import fnmatch
import logging
from multiprocessing import Process, Queue

import typing as t

from src.buildkite_agent import BuildkiteAgent
from src.buildkite_api import BuildkiteApi
from src.environment import Environment

logging.basicConfig()
logger = logging.getLogger(__name__) 

APPROVAL_VALIDATION_FAILED_EXIT_CODE = 99
FAILED_EMOJI = ":negative_squared_cross_mark:"
SUCCESS_EMOJI = ":white_check_mark:"

TIMER_EXPIRED_EVENT = "timer_expired"
OVERRIDE_EVENT = "override_step_unblocked"
NO_JOBS_REMAINING_EVENT = "no_unblockable_jobs_remaning"


def sleep(seconds: int) -> None:
    time.sleep(float(seconds))


class MultiUnblockPlugin:
    def __init__(
        self, env: Environment, api: BuildkiteApi, agent: BuildkiteAgent
    ) -> None:
        self.env = env
        self.api = api
        self.agent = agent

    def _poll_override_step_state_thread(
        self, step_key: str, result_queue: Queue
    ) -> None:
        poll_interval_seconds = 10
        while True:
            step_state = self.agent.get_step_state(step_key)
            logger.info(f"Override step state: {step_state}")
            if step_state in ["unblocked", "finished"]:
                result_queue.put(OVERRIDE_EVENT)
                break
            logger.info(
                f"Override step is still blocked, checking again in {poll_interval_seconds} seconds"
            )
            time.sleep(float(poll_interval_seconds))

    def _sleep_thread(self, seconds: int, result_queue: Queue) -> None:
        sleep(seconds)
        result_queue.put(TIMER_EXPIRED_EVENT)

    def _monitor_thread(self, override_step_key: str, result_queue: Queue) -> None:
        poll_interval_seconds = 10
        while True:
            logger.info("Checking for unblockable jobs")
            unblockable_jobs = self.api.get_unblockable_jobs_in_build(
                self.env.pipeline_slug, self.env.build_number
            )
            jobs_minus_override = [
                j for j in unblockable_jobs if j.step_key != override_step_key
            ]

            if not jobs_minus_override:
                logger.info("No remaining unblockable jobs. Exiting...")
                result_queue.put(NO_JOBS_REMAINING_EVENT)
                break
            logger.info(
                f"Found {len(jobs_minus_override)} unblockable jobs: {', '.join([j.step_key for j in jobs_minus_override])}"
            )
            time.sleep(float(poll_interval_seconds))

    def unblock_jobs(
        self,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
        override_step_key: t.Optional[str] = None,
    ) -> None:
        unblockable_jobs = self.api.get_unblockable_jobs_in_build(
            self.env.pipeline_slug, self.env.build_number
        )
        step_keys_to_unblock = set(block_steps)

        if override_step_key is not None:
            step_keys_to_unblock.add(override_step_key)

        if block_step_pattern:
            pattern_matched_step_keys = set(
                fnmatch.filter(
                    [j.step_key for j in unblockable_jobs], block_step_pattern
                )
            )
            logger.debug(f"Step Keys Matching Pattern: {block_step_pattern}")
            logger.debug(f"Key: {' '.join(pattern_matched_step_keys)}")
            step_keys_to_unblock.update(pattern_matched_step_keys)

        unblock_processes: t.List[Process] = []
        jobs_to_unblock = [
            j for j in unblockable_jobs if j.step_key in step_keys_to_unblock
        ]
        job_keys_to_unblock = [j.step_key for j in jobs_to_unblock]
        logger.info(f"Unblocking the following jobs: {', '.join(job_keys_to_unblock)}")
        for job in jobs_to_unblock:
            unblock_process = Process(target=self.api.unblock_job, args=[job])
            unblock_processes.append(unblock_process)

        # Start all threads.
        for p in unblock_processes:
            p.start()

        # Wait for all threads to finish.
        for p in unblock_processes:
            p.join()

    def timed_unblock_jobs(
        self,
        timeout_seconds: int,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
    ) -> None:
        sleep(timeout_seconds)
        self.unblock_jobs(block_steps, block_step_pattern)

    def timed_unblock_jobs_with_override(
        self,
        timeout_seconds: int,
        override_step_key: str,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
    ) -> None:
        processes: t.List[Process] = []
        result_queue = Queue()

        poll_override_state_process = Process(
            target=self._poll_override_step_state_thread,
            args=[override_step_key, result_queue],
        )
        poll_override_state_process.start()
        processes.append(poll_override_state_process)

        if timeout_seconds == -1:
            logger.info("Starting build monitor")
            monitor_process = Process(
                target=self._monitor_thread,
                args=[override_step_key, result_queue],
            )
            monitor_process.start()
            processes.append(monitor_process)
        else:
            logger.info("Starting timeout clock")
            timeout_process = Process(
                target=self._sleep_thread, args=[timeout_seconds, result_queue]
            )
            timeout_process.start()
            processes.append(timeout_process)

        result = result_queue.get()

        logger.info(f"Unblocking. Reason: {result}")

        for process in processes:
            process.terminate()
        self.unblock_jobs(block_steps, block_step_pattern, override_step_key)

    def main(self) -> None:
        if self.env.timeout_seconds is None:
            # No timer aspect, so immediately unblock
            logger.info("Immediately unblocking")
            self.unblock_jobs(self.env.block_steps, self.env.block_step_pattern)
        else:
            self_step_label = self.agent.get_self_step_label()
            if self.env.timeout_seconds == -1:
                self_step_label = f"{self_step_label} (Monitoring Build)"
            else:
                self_step_label = f"{self_step_label} (Unblocks after {self.env.timeout_seconds} seconds)"
            self.agent.update_self_step_label(self_step_label)

            if self.env.override_step_key is None:
                # Timer, but no override - sleep and then unblock everything
                logger.info("Unblocking after timer expires")
                self.timed_unblock_jobs(
                    self.env.timeout_seconds,
                    self.env.block_steps,
                    self.env.block_step_pattern,
                )
            else:
                logger.info("Unblocking after timer expires (with override)")
                self.timed_unblock_jobs_with_override(
                    self.env.timeout_seconds,
                    self.env.override_step_key,
                    self.env.block_steps,
                    self.env.block_step_pattern,
                )


if __name__ == "__main__":
    env = Environment()
    env.validate()
    api = BuildkiteApi(env.api_token, env.org)
    agent = BuildkiteAgent()
    plugin = MultiUnblockPlugin(env, api, agent)
    plugin.main()
