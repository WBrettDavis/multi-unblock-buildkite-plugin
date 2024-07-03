import os
import typing as t
from src.buildkite_agent import BuildkiteAgent
from src.buildkite_api import BuildkiteApi
from src.environment import Environment
from multiprocessing import Process, Queue
import time
import re

APPROVAL_VALIDATION_FAILED_EXIT_CODE = 99
FAILED_EMOJI = ":negative_squared_cross_mark:"
SUCCESS_EMOJI = ":white_check_mark:"


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
            print(f"Evaluating step state {step_state} for step: {step_key}")
            if step_state == "blocked":
                print(
                    f"Step is still blocked, checking again in {poll_interval_seconds} seconds"
                )
                time.sleep(float(poll_interval_seconds))
            else:
                result_queue.put("override_step_unblocked")

    def _sleep_thread(self, seconds: int, result_queue: Queue) -> None:
        time.sleep(seconds)
        result_queue.put("timer_expired")

    def unblock_jobs(
        self,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
    ) -> None:
        unblockable_jobs = self.api.get_unblockable_jobs_in_build(
            self.env.pipeline_slug, self.env.build_number
        )
        matched_jobs = []
        for job in unblockable_jobs:
            print(f"Evaluating job with step_key: {job.step_key}")
            if block_step_pattern and re.match(block_step_pattern, job.step_key):
                matched_jobs.append(job)
            elif job.step_key in block_steps:
                matched_jobs.append(job)
        unblock_processes: t.List[Process] = []
        for job in matched_jobs:
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
        seconds: float,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
    ) -> None:
        sleep(seconds)
        self.unblock_jobs(block_steps, block_step_pattern)

    def timed_unblock_jobs_with_override(
        self,
        timeout_seconds: int,
        block_steps: t.List[str],
        block_step_pattern: t.Optional[str],
        override_step_key: t.Optional[str],
    ) -> None:
        processes: t.List[Process] = []
        result_queue = Queue()

        poll_process = Process(
            target=self._poll_override_step_state_thread,
            args=[override_step_key, result_queue],
        )
        poll_process.start()

        timeout_process = Process(
            target=self._sleep_thread, args=[timeout_seconds, result_queue]
        )
        timeout_process.start()

        processes.extend([poll_process, timeout_process])

        result = result_queue.get()

        print(f"Unblocking. Reason: {result}")

        for process in processes:
            process.terminate()
        self.unblock_jobs(block_steps, block_step_pattern)

    def main(self) -> None:
        if self.env.timeout_seconds is None:
            # No timer aspect, so immediately unblock
            print("Immediately unblocking")
            self.unblock_jobs(self.env.block_steps, self.env.block_step_pattern)
        else:
            self_step_label = self.agent.get_self_step_label()
            self.agent.update_self_step_label(
                f"{self_step_label} (Unblocks after {self.env.timeout_seconds} seconds)"
            )
            if self.env.override_step_key is None:
                # Timer, but no override - sleep and then unblock everything
                print("Unblocking after timer expires")
                self.timed_unblock_jobs(
                    self.env.timeout_seconds,
                    self.env.block_steps,
                    self.env.block_step_pattern,
                )
            else:
                print("Unblocking after timer expires (with override)")
                self.timed_unblock_jobs_with_override(
                    self.env.timeout_seconds,
                    self.env.block_steps,
                    self.env.block_step_pattern,
                    self.env.override_step_key,
                )

        jobs = self.api.get_unblockable_jobs_in_build(
            self.env.pipeline_slug, self.env.build_number
        )
        print(f"Found {len(jobs)} unblockable jobs")
        for job in jobs:
            self.api.unblock_job(job)


if __name__ == "__main__":
    print("PLUGIN ENVIRONMENT")
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))
    
    env = Environment()
    env.validate()
    api = BuildkiteApi(env.api_token, env.org)
    agent = BuildkiteAgent()
    plugin = MultiUnblockPlugin(env, api, agent)
    plugin.main()
