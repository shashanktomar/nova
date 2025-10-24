# Just examples are here: https://github.com/casey/just/tree/master/examples
# Just docs are here: https://just.systems/man/en/introduction.html

# List all recipes
default:
    @just --list

# Read Python version from .python-version file
python_version := `cat ".python-version"`


###############################################
################## Dev Workflows ##############
###############################################

# Sync the project's dependencies with the environment.
[group('dev')]
sync:
    uv sync --all-groups

###############################################
################## CLI Commands ###############
###############################################

# Run the nova cli command
nova *args:
    uv run nova {{args}}

# Run manual marketplace CLI tests
[group('cli')]
test-marketplace-manual:
    ./scripts/test-marketplace-cli.sh

# aliases

alias t := test
alias te := test-e2e
alias tu := test-unit

###############################################
############# Testing and Linting #############
###############################################

# Run tests
[group('test and lint')]
test-e2e:
    uv run pytest -m e2e

[group('test and lint')]
test-unit:
    uv run pytest -m "not e2e"

[group('test and lint')]
test: test-unit test-e2e

# Run tests with coverage report
[group('test and lint')]
test-cov:
    uv run pytest --cov=src/nova --cov-report=term-missing --cov-report=html

# Format code
[group('test and lint')]
format:
    uv tool run ruff check --fix && uv tool run ruff format

# Run linter
[group('test and lint')]
lint:
    uv tool run ruff check

# Run type checker
[group('test and lint')]
check-types:
    uv run pyright

# Check if the lockfile is up-to-date
[group('test and lint')]
lockfile-check:
  uv lock --check

# Run all code quality checks
[group('test and lint')]
lint-all: lockfile-check lint check-types
    @echo "All lint checks passed! 🎉"

# Run test and all code quality checks
[group('test and lint')]
check: lint-all test

###############################################
############### Utilities #####################
###############################################

# Setup project on new dev machine (idempotent)
[group('utils')]
setup: install-uv
  command -v ruff >/dev/null 2>&1 || uv tool install ruff
  just sync

# View the dependency tree for the project.
[group('utils')]
tree:
  uv tree

# Remove cache entries
[group('utils')]
clean:
  uv cache clean

# Upgrade tools
[group('utils')]
update-tools:
  uv tool upgrade --all

###############################################
############### Private #####################
###############################################

[macos, private]
install-uv:
  command -v uv >/dev/null 2>&1 || brew install uv

[linux, private]
install-uv:
  command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
