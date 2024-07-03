# Multi Approval Buildkite Plugin

Buildkite plugin to allow pipelines to handle block and input steps more dynamically.

## Examples

### Unblock Input or Block steps after a fixed amount of time

Add the following to your `pipeline.yml`:

```yml
steps:
    - label: Automatically unblock all deploys after 30 seconds
      plugins:
        - seek-oss/aws-sm#v2.3.1:
            env:
              BUILDKITE_API_TOKEN: buildkite/api
        - wbrettdavis/multi-unblock:
            timeout-seconds: 30
            block-steps:
              - unblock-us-deploy
              - unblock-eu-deploy
    - input: "Start US deployment"
      key: unblock-us-deploy
    - command: "deploy.sh --region US'"
      depends_on:
        - unblock-us-deploy
    - input: "Start EU deployment"
      key: unblock-eu-deploy
    - command: "deploy.sh --region EU'"
      depends_on:
        - unblock-eu-deploy
```

### Create an Input Step to Unblock Multiple Input Steps

Add the following to your `pipeline.yml`:

```yml
steps:
    - input: "Click here to unblock all deployments"
      key: "unblock-all"
    - label: Unblock all deployments  
      plugins:
        - seek-oss/aws-sm#v2.3.1:
            env:
              BUILDKITE_API_TOKEN: buildkite/api
        - wbrettdavis/multi-unblock:
            timeout-seconds: -1
            block-step-pattern: unblock-*-deploy
            override-step-key: unblock-all
    - input: "Start US deployment"
      key: unblock-us-deploy
    - command: "deploy.sh --region US'"
      depends_on:
        - unblock-us-deploy
    - input: "Start EU deployment"
      key: unblock-eu-deploy
    - command: "deploy.sh --region EU'"
      depends_on:
        - unblock-eu-deploy
```

### Automatically run all steps with fixed delay between them, allow one or all to be unblocked manually

Add the following to your `pipeline.yml`:

```yml
steps:
    - input: "Click here to unblock all deployments"
      key: "unblock-all"
    - label: Unblock all deployments  
      plugins:
        - seek-oss/aws-sm#v2.3.1:
            env:
              BUILDKITE_API_TOKEN: buildkite/api
        - wbrettdavis/multi-unblock:
            timeout-seconds: -1
            block-step-pattern: unblock-*-deploy
            override-step-key: unblock-all

    - label: Automatically start US deployment after 30 seconds if not unblocked 
      plugins:
        - seek-oss/aws-sm#v2.3.1:
            env:
              BUILDKITE_API_TOKEN: buildkite/api
        - wbrettdavis/multi-unblock:
            timeout-seconds: 30
            override-step-key: unblock-us-deploy
    - input: "Start US deployment"
      key: unblock-us-deploy
    - command: "deploy.sh --region US'"
      depends_on:
        - unblock-us-deploy

    - label: Automatically start EU deployment after 30 seconds if not unblocked 
      plugins:
        - seek-oss/aws-sm#v2.3.1:
            env:
              BUILDKITE_API_TOKEN: buildkite/api
        - wbrettdavis/multi-unblock:
            timeout-seconds: 30
            override-step-key: unblock-eu-deploy
    - input: "Start EU deployment"
      key: unblock-eu-deploy
    - command: "deploy.sh --region EU'"
      depends_on:
        - unblock-eu-deploy
```

## Configuration

### `timeout-seconds` (Optional, int)

Sets the number of seconds the step will wait before force-unblocking all input and block steps with keys matched by either `block-steps` or `block-step-pattern`. 

Set to `-1` to have the plugin step continuously poll the build state to determine if any steps should be force-unblocked due to an override for the lifetime of the build.

### `block-steps` (Optional, array)

This array contains a list of strings exactly matching the `key` of Input or Block steps which should be unblocked by the plugin when conditions are met.

## `block-step-pattern` (Optional, string)

This string represents a glob-like pattern supporting wildcards. Any `Input` or `Block` steps with `key` values matching this pattern will be unblocked when the plugin conditions are met.

### `override-step-key` (Required, string)

This is the key of the step that will be monitored by the plugin for determining if it should immediately unblock the targeted `Input` or `Block` steps. As soon as the step with this key is unblocked, the plugin will immediately cancel and timers or monitoring processes, unblock the targeted steps, and exit.

### `api-token` (Optional, string)

This plugin must make calls to the Buildkite REST API and must have access to a valid Buildkite API token with the following scopes:
- `write_builds`
- `read_builds`

If the `api-token` value is specified, it should be the name of the *Environment Variable* where the Buildkite API token is set on the Buildkite Agent running the plugin step. If not specified, it will default to looking for the API token in an environment variable named `BUILDKITE_API_TOKEN`.

Best practice here dictates that the API token should be read from some an external Secret Store, such as AWS Secrets Manager.


## Developing
Be careful when adding references to new Python libraries to this plugin. All Python libraries used should be part of the standard library and pre-installed on Buildkite agent AMIs.

### To run the basic PyTest suite (fast):
1. Create a venv and install the requirements from `requirements-dev.txt` if you haven't already done so


```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

1. Run pytest

```shell
python -m pytest tests
```

### To run the full PyTest suite in across different pristine python environments using Docker:

```shell
./scripts/test.sh
```