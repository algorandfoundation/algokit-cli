
import json

from algokit.core.sandbox import get_conduit_yaml, get_config_json, get_docker_compose_yml

from tests.utils.approvals import verify


def test_get_config_json() -> None:
    config_json = json.loads(get_config_json())
    verify(json.dumps(config_json, indent=2))


def test_get_conduit_yaml() -> None:
    conduit_yaml = get_conduit_yaml()
    verify(conduit_yaml)

def test_get_docker_compose_yml() -> None:
    docker_compose_yml = get_docker_compose_yml()
    verify(docker_compose_yml)
