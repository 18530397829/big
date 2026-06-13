from pathlib import Path

import yaml


def test_docker_compose_defines_postgres_and_redis() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))

    assert "postgres" in compose["services"]
    assert "redis" in compose["services"]
