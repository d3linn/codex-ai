#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH="${PYTHONPATH:-.}" pytest --cov=app --cov-report=term-missing "$@"
