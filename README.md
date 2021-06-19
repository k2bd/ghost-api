# API for 2D Ghost

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

Nicely rendered API docs are then available on http://127.0.0.1:8000/redoc
