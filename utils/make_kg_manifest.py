# make_kg_manifest.py

"""Utility for generating KG-Hub Manifest file,
containing a list of all graphs and subgraphs
(i.e., full KGs and graphs of transformed sources)
for all KG-Hub projects.
The Manifest file follows the LinkML Datasets
schema as defined here:
https://github.com/linkml/linkml-model/blob/main/linkml_model/model/schema/datasets.yaml
Objects have unique IDs that are URLs.

This script also performs some validations on 
file and directory structure, format, and content.
"""

import boto3
import botocore.exceptions
import botocore.errorfactory
import click
import requests
import yaml

import os
from datetime import datetime

from linkml_runtime.dumpers import yaml_dumper

# LinkML classes
import datasets
from datasets import DataPackage, DataResource

# List of all current, fully defined projects on KG-Hub
# Other projects will still be indexed,
# but won't have versions or descriptions 
# assigned in the manifest unless they are here.
PROJECTS = {"kg-obo": "KG-OBO: OBO ontologies into KGX TSV format.",
            "kg-idg": "KG-IDG: a Knowledge Graph for Illuminating the Druggable Genome.",
            "kg-covid-19": "KG-COVID-19: a knowledge graph for COVID-19 and SARS-COV-2.",
            "kg-microbe": "KG-Microbe: a knowledge graph for microbial traits.",
            "eco-kg": "eco-KG: a knowledge graph of plant traits starting with Planteome and EOL TraitBank.",
            "monarch": "Graph representation of the Monarch Initiative knowledge resource."}

# List of component types used to build larger KGs
SUBGRAPH_TYPES = ["raw",
                "transformed"]

# List of Directories to ignore, as we can't verify their 
# contents are all in the expected format
IGNORE_DIRS = ["attic",
                "frozen_incoming_data",
                "embeddings",
                "kg-covid-19-sparql",
                "ontoml",
                "test"]

@click.command()
@click.option("--bucket",
               required=True,
               nargs=1,
               help="""The name of an AWS S3 bucket to generate Manifest for.""")
@click.option("--outpath",
               required=True,
               nargs=1,
               help="""Name or path to the manifest file to be written.""")
def run(bucket: str, outpath: str):

    #TODO: download any existing manifest with the same name
    #       as outpath from the bucket.
    #       We will overwrite it locally but read it first
    #       To retain all existing records and update if needed

    # Get the OBO Foundry YAML so we can cross-reference KG-OBO
    obo_metadata = retrieve_obofoundry_yaml()

    project_metadata = {"kg-obo":obo_metadata}

    try:
        keys = list_bucket_contents(bucket)
        project_contents = validate_projects(keys)
        graph_file_keys = get_graph_file_keys(keys)
        dataset_objects = create_dataset_objects(graph_file_keys, 
                                                project_metadata,
                                                project_contents)
        write_manifest(dataset_objects, outpath)
    except botocore.exceptions.NoCredentialsError:
        print("Can't find AWS credentials.")

def list_bucket_contents(bucket: str):
    """Lists all contents, keys only, of an AWS S3 bucket.
    :param bucket: name of the bucket
    :return: list of all keys, as strings, in the bucket"""
    
    all_object_keys = []

    client = boto3.client('s3')

    pager = client.get_paginator("list_objects_v2")

    print(f"Searching \x1b[32m{bucket}\x1b[0m...")
    for page in pager.paginate(Bucket=bucket):
        remote_contents = page['Contents']
        for key in remote_contents:
            all_object_keys.append(key['Key'])

    print(f"Bucket \x1b[32m{bucket}\x1b[0m contains {len(all_object_keys)} objects.")

    return all_object_keys

def validate_build_name(build_name: str):
    """Given a string, ensures it matches an expected
    date format.
    Returns True if matched, False if not.
    :param build_name: str, the name of the build
    """

    try:
        datetime.strptime(build_name, '%Y%m%d')
        return True
    except ValueError:
        return False

def validate_projects(keys: list) -> None:
    """Given a list of keys, verifies the following:
        * Projects follow the expected file structure of 
            dated builds, 
            raw and transforms in their own dirs, 
            and stats in their own dir
        * Graph tar.gz files contain only node and edge list
        * Files are, in fact, tsvs in KGX format.
    All output is to STDOUT.
    This assumes everything in the root of the project
    directory is a build, but valid builds must
    meet the above criteria.
    :param keys: list of object keys, as strings
    :return: dict, project_contents with keys as project names, 
                values are dicts
    """

    project_contents = {}

    # Iterate through all keys for each project,
    # then go back and iterate through individual builds only
    # to validate
    for project_name in PROJECTS:
        if project_name == "kg-obo": 
            continue # Don't validate KG-OBO, it has its own validators
        project_contents[project_name] = {"objects":[],
                                            "builds": [],
                                            "valid builds":[],
                                            "incorrectly named builds":[],
                                            "incorrectly structured builds":[],
                                            "builds with too many files in tar.gz":[],
                                            "builds with KGX format problems":[]}
        print(f"Validating {project_name}...")
        for keyname in keys:
            try:
                project_dirname = (keyname.split("/"))[0]
                if project_dirname == project_name: # This is the target project
                    project_contents[project_name]["objects"].append(keyname)

                    # Now collect all builds
                    build_name = (keyname.split("/"))[1]
                    if build_name not in project_contents[project_name]["builds"] and \
                        build_name not in ["index.html", "current","README"]:
                        project_contents[project_name]["builds"].append(build_name)

            except IndexError:
                pass
        
        # Iterate through builds now to validate
        for build_name in project_contents[project_name]["builds"]:
            valid = True

            if not validate_build_name(build_name):
                valid = False
                project_contents[project_name]["incorrectly named builds"].append(build_name)

            for dir_type in ["raw","stats","transformed"]:
                dir_index = f"{project_name}/{build_name}/{dir_type}/index.html"
                if not dir_index in keys:
                    valid = False
                    if build_name not in project_contents[project_name]["incorrectly structured builds"]:
                        project_contents[project_name]["incorrectly structured builds"].append(build_name)

            #TODO: download and open each graph tar.gz to verify:
            #       1. only node and edge file within
            #       2. files are tsvs with a header
            # Use kgx validate

            if valid:
                project_contents[project_name]["valid builds"].append(build_name)

        print(f"The project {project_name} contains:")
        for object_type in project_contents[project_name]:
            object_count = len(project_contents[project_name][object_type])
            if object_count > 0:
                print(f"\t{object_count} {object_type}")
                if object_type in ["incorrectly named builds",
                                    "incorrectly structured builds",
                                    "builds with too many files in tar.gz",
                                    "builds with KGX format problems"]:
                    invalid_builds = project_contents[project_name][object_type]
                    print(f"\t\t{invalid_builds}")
        
    return project_contents

def get_graph_file_keys(keys: list):
    """Given a list of keys, returns a list of those
    resembling graphs.
    :param keys: list of object keys, as strings
    :return: dict of all keys appearing to be graph files,
            with keys denoting `compressed` or `uncompressed`.
            Values are lists of strings."""
    
    graph_file_keys = {"compressed":[],"uncompressed":[]}

    for keyname in keys:
        try:
            if (keyname.split("/"))[0] in IGNORE_DIRS:
                continue
        except IndexError:
            pass
        if keyname[-7:] == ".tar.gz":
            graph_file_keys["compressed"].append(keyname)
        if keyname[-9:] in ["edges.tsv", "nodes.tsv"]:
            graph_file_keys["uncompressed"].append(keyname)

    for object_type in graph_file_keys:
        print(f"Found {len(graph_file_keys[object_type])} {object_type} graph files.")

    return graph_file_keys

def create_dataset_objects(objects: list, project_metadata: dict, project_contents: dict):
    """Given a list of object keys, returns a list of
    LinkML-defined DataPackage objects.
    See datasets.py for class definitions.
    :param objects: list of object keys
    :param project_metadata: dict of parsed metadata for specific projects,
                            with project names as keys
    :param project_contents: dict with keys as project names values are dicts
    :return: list of DataPackage and DataResource objects with their values"""

    all_data_objects = []

    for object_type in objects:
        for object in objects[object_type]:
            url = "https://kg-hub.berkeleybop.io/" + object
            title = (object.split("/"))[-1]
            project_name = (object.split("/"))[0]
            build_name = (object.split("/"))[1]
      
            if object_type == "compressed":
                data_object = DataPackage(id=url,
                                    title=title,
                                    compression="tar.gz")
                if (object.split("/"))[0] in PROJECTS and \
                    (object.split("/"))[-2] not in SUBGRAPH_TYPES:
                    data_object.version = (object.split("/"))[-2]
                    data_object.description = PROJECTS[(object.split("/"))[0]]
                if (object.split("/"))[0] == "kg-obo":
                    for ontology in project_metadata["kg-obo"]:
                        if ontology['id'] == (object.split("/"))[1]:
                            data_object.description = f"{ontology['id'].upper()}. {ontology['description']}"
                            data_object.was_derived_from = ontology['ontology_purl']
                            try:
                                data_object.license = ontology['license']['label']
                                data_object.publisher = f"{ontology['contact']['label']} ({ontology['contact']['email']})"
                            except KeyError:
                                pass
            else:
                data_object = DataResource(id=url,
                                    title=title)

            # See if validation was passed for the corresponding build
            try:
                if build_name in project_contents[project_name]["valid builds"]:
                    data_object.conforms_to = "KG-Hub"
            except KeyError:
                pass

            # Identify original source name for transformed products
            try:
                if (object.split("/"))[-3] == "transformed":
                    data_object.was_derived_from = (object.split("/"))[-2]
            except IndexError:
                pass

            all_data_objects.append(data_object)

    return all_data_objects

def write_manifest(data_objects: list, outpath: str) -> None:
    """Given a list of LinkML-defined DataPackage objects,
    dumps them to a YAML file.
    If this file already exists, it is overwritten.
    :param data_objects: list of DataPackage and DataResource objects
    :param outpath: str, filename or path to write to
    """
    
    header = "# Manifest for KG-Hub graphs\n"

    with open(outpath, 'w') as outfile:
        outfile.write(header)
        outfile.write(yaml_dumper.dumps(data_objects))

    print(f"Wrote to {outpath}.")

def retrieve_obofoundry_yaml(
        yaml_url: str = 'https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/registry/ontologies.yml',
        skip: list = [],
        get_only: list = []) -> list:
    """ Retrieve YAML containing list of all ontologies in OBO Foundry
    :param yaml_url: a stable URL containing a YAML file that describes all the OBO ontologies
    :param skip: which ontologies should we skip
    :return: parsed yaml describing ontologies
    """

    onto_file_name = "ontologies.yaml"

    # Use cached yaml
    if os.path.exists(onto_file_name):
        print(f"Loading OBO metadata from cached {onto_file_name}...")
        with open(onto_file_name) as infile:
            yaml_parsed = yaml.safe_load(infile)
            yaml_onto_list: list = yaml_parsed['ontologies']

    else: # Retrieve and save
        print(f"Retrieving OBO metadata from {yaml_url}...")

        yaml_req = requests.get(yaml_url)
        yaml_content = yaml_req.content.decode('utf-8')
        yaml_parsed = yaml.safe_load(yaml_content)
        if not yaml_parsed or 'ontologies' not in yaml_parsed:
            raise RuntimeError(f"Can't retrieve ontology info from YAML at this url {yaml_url}")
        else:
            yaml_onto_list: list = yaml_parsed['ontologies']
        
        with open(onto_file_name, 'w') as outfile:
            yaml.dump(yaml_parsed, outfile)

    if len(skip) > 0:
        yaml_onto_list_filtered = \
            [ontology for ontology in yaml_onto_list if ontology['id'] not in skip \
            if ("is_obsolete" not in ontology) or (ontology['is_obsolete'] == False)
            ]
    elif len(get_only) > 0:
        yaml_onto_list_filtered = \
            [ontology for ontology in yaml_onto_list if ontology['id'] in get_only \
            if ("is_obsolete" not in ontology) or (ontology['is_obsolete'] == False)
            ]
    else:
        yaml_onto_list_filtered = \
            [ontology for ontology in yaml_onto_list \
            if ("is_obsolete" not in ontology) or (ontology['is_obsolete'] == False)
            ]

    return yaml_onto_list_filtered

if __name__ == '__main__':
  run()