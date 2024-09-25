#!/bin/bash
# Assemble files for KG-Hub site

# Define paths
PROJECT_FILE="projects.yaml"
MANIFEST_URL="https://kghub.io/MANIFEST.yaml"
MANIFEST_FILE="MANIFEST.yaml"
KGOBO_URL="https://kghub.io/kg-obo/tracking.yaml"
KGOBO_FILE="tracking.yaml"

# Retrieve most recent MANIFEST and do some format prep
# wget -N $MANIFEST_URL
# sed -i -e 's/^/  /' $MANIFEST_FILE
# sed -i '1s/^/manifest:\n /' $MANIFEST_FILE

# Set up redirects as needed
# python make_redirect.py

# Retrieve KG-OBO tracking file - this has its own metadata
# But it needs to be processed to be included on the site
wget -N $KGOBO_URL
python process_kgobo.py
