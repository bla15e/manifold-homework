#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# Main logic of script
cd "$(dirname "$0")"

main() {
    docker run -p 5000:5000 registry:2
}

main "$@"
