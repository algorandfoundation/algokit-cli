#!/bin/bash

# Ensure the script fails on errors
set -e

# Check if the correct number of arguments are passed
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <destination_directory> <release_tag> <artifact_path>"
  exit 1
fi

# Assign arguments to variables
DESTINATION_DIR="$1"
RELEASE_TAG="$2"
ARTIFACT_PATH="$3"
GRADE="$4"

# Ensure the destination directory exists
mkdir -p "${DESTINATION_DIR}/snap"

# Extract version from RELEASE_TAG, assuming it's in the format "vX.Y.Z"
VERSION="${RELEASE_TAG#v}"

# Use the provided ARTIFACT_PATH
SOURCE="$ARTIFACT_PATH"

# Create the snapcraft.yaml file
cat > "${DESTINATION_DIR}/snap/snapcraft.yaml" <<EOF
name: algokit
version: "$VERSION"
summary: The AlgoKit CLI is the one-stop shop tool for developers building on Algorand
description: |
  AlgoKit gets developers of all levels up and running with a familiar, 
  fun and productive development environment in minutes. 
  The goal of AlgoKit is to help developers build and launch 
  secure, automated production-ready applications rapidly.

base: core22
confinement: classic
grade: $GRADE

parts:
  algokit:
    plugin: dump
    source: $SOURCE

apps:
  algokit:
    command: algokit
    plugs: [home, network]
EOF

echo "snapcraft.yaml has been created at ${DESTINATION_DIR}/snap/snapcraft.yaml"
   