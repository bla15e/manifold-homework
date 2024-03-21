#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# Main logic of script
cd "$(dirname "$0")"

main() {
    cd ../server
    docker compose build
    docker compose up
}

main "$@"
