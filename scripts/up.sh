#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# Main logic of script
cd "$(dirname "$0")"

main() {
    cd "../"
    minikube start --driver docker --static-ip 192.168.200.200
}

main "$@"
