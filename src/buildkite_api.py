import json
import logging
import urllib.parse
import urllib.request
import urllib.error
import typing as t

logging.basicConfig()
logger = logging.getLogger(__name__) 

class BuildkiteUser:
    def __init__(self, id, name: str, email: str) -> None:
        self.id = id
        self.name = name
        self.email = email

    def __repr__(self) -> str:
        return f"{self.name}({self.email})"


class BuildkiteJob:
    def __init__(
        self,
        id: str,
        step_key: t.Optional[str],
        unblockable: t.Optional[bool],
        state: t.Optional[str],
        unblock_url: t.Optional[str],
    ) -> None:
        self.id = id
        self.step_key = step_key
        self.unblockable = unblockable
        self.state = state
        self.unblock_url = unblock_url

    @staticmethod
    def from_json(json: dict) -> "BuildkiteJob":
        return BuildkiteJob(
            id=json["id"],
            step_key=json.get("step_key", None),
            unblockable=json.get("unblockable", None),
            state=json.get("state", None),
            unblock_url=json.get("unblock_url", None),
        )

    def __repr__(self) -> str:
        return f"step_key: {self.step_key}, unblockable: {self.unblockable} state: {self.state} unblock_url: {self.unblock_url}"


class BuildkiteBuild:
    def __init__(self, id: str, jobs: t.List[BuildkiteJob]) -> None:
        self.jobs = jobs

    @staticmethod
    def from_json(json: dict) -> "BuildkiteBuild":
        return BuildkiteBuild(
            id=json["id"], jobs=[BuildkiteJob.from_json(j) for j in json["jobs"]]
        )


BUILDKITE_API_URL = "https://api.buildkite.com/v2"


class BuildkiteApi:
    def __init__(self, api_token: str, org: str) -> None:
        self.org = org
        self.api_token = api_token

    def _auth_headers(self) -> t.Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}"}

    def _send_request(self, req: urllib.request.Request) -> t.Tuple[int, dict, t.Any]:
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read()
                response_object = json.loads(data.decode("utf-8"))
                return (response.status, response.headers, response_object)
        except urllib.error.HTTPError as e:
            return (e.code, e.headers, e.read())

    def _http_get(
        self, url
    ) -> t.Tuple[
        int, dict, t.Any
    ]:  # Returns (status_code, response headers, json data)
        req = urllib.request.Request(
            url=url, headers=self._auth_headers(), method="GET"
        )
        return self._send_request(req)

    def _http_put(
        self, url: str, data: t.Optional[dict] = None
    ) -> t.Tuple[
        int, dict, t.Any
    ]:  # Returns (status_code, response headers, json data)
        headers = {**self._auth_headers(), **{"Content-Type": "application/json"}}
        req = urllib.request.Request(
            url=url,
            data=json.dumps(data).encode("utf-8") if data is not None else None,
            headers=headers,
            method="PUT",
        )
        return self._send_request(req)

    def get_unblockable_jobs_in_build(
        self, pipeline_slug: str, build_number: int
    ) -> t.List[BuildkiteJob]:
        builds_api = (
            f"organizations/{self.org}/pipelines/{pipeline_slug}/builds/{build_number}"
        )
        url = f"{BUILDKITE_API_URL}/{builds_api}"
        status_code, res_headers, build_json = self._http_get(url)
        logger.debug(f"(BK API) get_unblockable_jobs_in_build Response: ({status_code}, {res_headers}, {build_json})")
        build = BuildkiteBuild.from_json(build_json)
        unblockable_jobs = [j for j in build.jobs if j.unblockable]
        return unblockable_jobs

    def unblock_job(
        self, job: BuildkiteJob, fields: t.Optional[t.Dict[str, str]] = None
    ) -> None:
        if not job.unblock_url:
            raise Exception("Job has no unblock_url set")
        if not fields:
            fields = {}
        status_code, res_headers, data = self._http_put(job.unblock_url, data=fields)
        logger.debug(f"(BK API) unblock_job Response: ({status_code}, {res_headers}, {data})")
