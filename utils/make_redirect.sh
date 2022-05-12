#!/bin/bash
# Make one or more redirects on S3 + Cloudfront
# Reads the updated KG-Hub MANIFEST to find
# any download_url values - then creates redirects
# with s3cmd
# Must pass the path to the MANIFEST as an argument, e.g.
# sh make_redirect.sh "../docs/MANIFEST.yaml"

echo "Reading $1 to find redirects..."

# Get all download_url values first
new_urls=$(grep "download_url:" "$1" | cut -f6 -d' ') 

echo $new_urls

# Get corresponding object id for each - that's the old url

# Now set the redirect
#s3cmd --acl-public --add-header "x-amz-website-redirect-location: /new-url" --no-preserve put "./old-url" "s3://domain.com/new-url"