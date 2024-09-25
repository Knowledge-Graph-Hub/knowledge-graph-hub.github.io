"""KG-OBO tracking file processing."""

import yaml

TRACKING_FILE = "tracking.yaml"
PROCESSED_FILE = "kg_obo_current.yaml"

# Load the tracking file
with open(TRACKING_FILE) as infile:
    tracking = yaml.safe_load(infile)

# For each ontology in the list
processed_list = []
for ontology in tracking["ontologies"]:
    if "current_version" in tracking["ontologies"][ontology]:
        current_version = tracking["ontologies"][ontology]["current_version"]
    else:
        current_version = "Unknown"
    this_ontology = {
        "id": ontology,
        "OBO Foundry Page": f"<https://obofoundry.org/ontology/{ontology}>",
        "All Graph Versions": f"<https://kg-hub.berkeleybop.io/kg-obo/{ontology}/>",
        "Current Version": current_version,
    }
    processed_list.append(this_ontology)

# Save it
with open(PROCESSED_FILE, "w") as outfile:
    yaml.dump(data=processed_list, stream=outfile, sort_keys=False)
