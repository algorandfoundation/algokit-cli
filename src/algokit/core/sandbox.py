def get_docker_compose_yml(
    name: str = "algokit",
    algod_port: int = 4001,
    kmd_port: int = 4002,
    tealdbg_port: int = 9392,
    indexer_port: int = 8980,
) -> str:
    return f"""version: '3'

services:
  algod:
    container_name: {name}_algod
    image: makerxau/algorand-sandbox-dev:latest
    ports:
      - {algod_port}:4001
      - {kmd_port}:4002
      - {tealdbg_port}:9392

  indexer:
    container_name: {name}_indexer
    image: makerxau/algorand-indexer-dev:latest
    ports:
      - {indexer_port}:8980
    restart: unless-stopped
    environment:
      ALGOD_HOST: algod
      POSTGRES_HOST: indexer-db
      POSTGRES_PORT: 5432
      POSTGRES_USER: algorand
      POSTGRES_PASSWORD: algorand
      POSTGRES_DB: indexer_db
    depends_on:
      - indexer-db
      - algod

  indexer-db:
    container_name: {name}_postgres
    image: postgres:13-alpine
    user: postgres
    environment:
      POSTGRES_USER: algorand
      POSTGRES_PASSWORD: algorand
      POSTGRES_DB: indexer_db
"""
