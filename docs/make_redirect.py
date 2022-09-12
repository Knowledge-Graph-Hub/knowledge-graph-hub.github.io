# make_redirect.py

'''
Make one or more redirects on S3 + Cloudfront
Reads the updated KG-Hub MANIFEST to find
any download_url values - then creates redirects
with s3cmd
Assumes the manifest file will be present at
MANIFEST.yaml
'''

import sh
import yaml

MANIFEST = "MANIFEST.yaml"

print(f"Reading {MANIFEST} to find redirects...")

redirects = {}

# Parse the input
# Get corresponding object id for each - that's the old url
# The new url is in download_url.
# Only KGs have this key/value pair.
with open(MANIFEST) as infile:
    yaml_parsed = yaml.safe_load(infile)
    for entry in yaml_parsed['manifest']:
        if 'download_url' in entry:
            new_url = entry['download_url']
            old_url = entry['id']
            redirects[old_url] = new_url
            print(f"Will redirect {old_url} to {new_url}.")

# Now set the redirect
for old_url in redirects:
    new_url = redirects[old_url]
    obj_id = "kg-hub-public-data/" + new_url[30:]
    sh.s3cmd("--acl-public",
             "modify",
             "--add-header", 
             f"x-amz-website-redirect-location:/{new_url}",
             f"s3://{obj_id}")