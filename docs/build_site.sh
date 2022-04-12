#!/bin/bash
# Assemble files for KG-Hub site

# Define paths
JEKYLL_CONFIG_HEADER_FILE="_config_header.yml"
JEKYLL_CONFIG_FILE="_config.yml"
PROJECT_FILE="../utils/projects.yaml"
MANIFEST_URL="https://kg-hub.berkeleybop.io/MANIFEST.yaml"
MANIFEST_FILE="MANIFEST.yaml"

# Retrieve most recent MANIFEST and do some format prep
wget -N $MANIFEST_URL
sed -i -e 's/^/  /' $MANIFEST_FILE
sed -i '1s/^/manifest:\n /' $MANIFEST_FILE

# Append projects list
echo "Adding all lists to Jekyll config."
cat $JEKYLL_CONFIG_HEADER_FILE $PROJECT_FILE $MANIFEST_FILE  > $JEKYLL_CONFIG_FILE