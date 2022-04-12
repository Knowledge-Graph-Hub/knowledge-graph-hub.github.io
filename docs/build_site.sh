#!/bin/bash
# Assemble files for KG-Hub site

# Define paths
JEKYLL_CONFIG_HEADER_FILE="_config_header.yml"
JEKYLL_CONFIG_FILE="_config.yml"
PROJECT_FILE="../utils/projects.yaml"
MANIFEST_URL="https://kg-hub.berkeleybop.io/MANIFEST.yaml"

# Retrieve most recent MANIFEST
wget -N $MANIFEST_URL

# Append projects list
echo "Adding project list to Jekyll config."
cat $JEKYLL_CONFIG_HEADER_FILE $PROJECT_FILE  > $JEKYLL_CONFIG_FILE