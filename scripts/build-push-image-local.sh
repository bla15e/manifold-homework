#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# Main logic of script
cd "$(dirname "$0")"

main() {
    cd ../server
    docker build . -t localhost:5000/homework-server
    docker push localhost:5000/homework-server
}

main "$@"
