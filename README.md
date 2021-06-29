[![CI](https://github.com/k2bd/ghost-api/actions/workflows/ci.yml/badge.svg)](https://github.com/k2bd/ghost-api/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/k2bd/ghost-api)](https://app.codecov.io/gh/k2bd/ghost-api)

# API for 2D Ghost

API and database service for my [2D Ghost App](https://ghost.k2bd.dev).

## What is 2D Ghost?

2D Ghost is a word game where players take turns building up words in a grid, trying to avoid completing words while trying to trap other players into completing words. (TODO: full description)

## Development
To get started, install [Poetry](https://python-poetry.org/), then `poetry install` the project

If Poetry is managing a virtual environment for you, you may have to replace `poe` with `poetry run poe` in the commands described below.

Docker is also required to run a local DynamoDB instance during tests and when running a development local server.

### Linting and running tests

To autoformat the code: `poe autoformat`

To run linting: `poe lint`

To run all tests: `poe test`

### Running a local development server

To start the testing DynamoDB instance and run a local development server: `poe local-server`

Nicely rendered API docs are then available on http://127.0.0.1:8000/redoc.

This also creates the games table so the API is functional for local apps.

(Note: if the server is terminated with keyboard interrupt then the DynamoDB instance will have to be torn down manually for now)
