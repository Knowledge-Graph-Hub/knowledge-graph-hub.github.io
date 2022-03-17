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
import tarfile
import sys
import logging

import os
import shutil
from datetime import datetime

import kgx.cli  # type: ignore

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils import strictness

# LinkML classes
import models.datasets
from models.datasets import GraphDataPackage, DataResource

# Helper functions
from get_kg_contents import retrieve_stats

# Load projects.yaml - this is the list of 
# all current, fully defined projects on KG-Hub.
# Other projects will still be indexed,
# but won't have versions or descriptions 
# assigned in the manifest unless they are here.
PROJECTS = {}
with open('projects.yaml') as infile:
    yaml_parsed = yaml.safe_load(infile)
    for project in yaml_parsed['projects']:
        PROJECTS[project['id']] = project['description']

# These projects won't get the full KGX validation.
VALIDATION_DENYLIST = ["kg-covid-19"]

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

# Set up logger - will write to STDOUT too
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
loghandler = logging.FileHandler('manifest.log')
consolehandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] - %(message)s',
                               datefmt='%a, %d %b %Y %H:%M:%S')
loghandler.setFormatter(formatter)
logger.addHandler(loghandler)
logger.addHandler(consolehandler)

@click.command()
@click.option("--bucket",
               required=True,
               nargs=1,
               help="""The name of an AWS S3 bucket to generate Manifest for.""")
@click.option("--outpath",
               required=True,
               nargs=1,
               help="""Name or path to the manifest file to be written.""")
@click.option("--maximum",
               type=int,
               nargs=1,
               help="""Maximum number of new resources to load during this run.
                        Most helpful when building manifest from scratch.
                        If not specified, all objects on the remote
                        will be considered.""")
def run(bucket: str, outpath: str, maximum = None):

    # Download any existing manifest from the bucket.
    # We read it first to retain all existing records and update if needed.
    # Most importantly, ignore graphs we already have builds for in the MANIFEST
    # so we don't spend a lot of time validating them again

    # Get the OBO Foundry YAML so we can cross-reference KG-OBO
    obo_metadata = retrieve_obofoundry_yaml()
    project_metadata = {"kg-obo":obo_metadata}

    manifest_name = os.path.basename(outpath)

    try:
        keys = list_bucket_contents(bucket)
        if os.path.basename(manifest_name) in keys: # Check if we have MANIFEST already
            logging.info("Found existing manifest. Will load and update.")
            previous_manifest = load_previous_manifest(bucket, manifest_name)
        else:
            previous_manifest = []
        graph_file_keys = get_graph_file_keys(keys, maximum, previous_manifest)
        project_contents = validate_projects(bucket, keys, graph_file_keys)
        dataset_objects = create_dataset_objects(graph_file_keys, 
                                                project_metadata,
                                                project_contents,
                                                previous_manifest)
        dataset_objects = get_stats(bucket, dataset_objects)
        dataset_objects = check_urls(bucket, dataset_objects)
        write_manifest(dataset_objects, outpath)
    except botocore.exceptions.NoCredentialsError:
        logging.error("Can't find AWS credentials.")

def list_bucket_contents(bucket: str):
    """Lists all contents, keys only, of an AWS S3 bucket.
    :param bucket: name of the bucket
    :return: list of all keys, as strings, in the bucket"""
    
    all_object_keys = []

    client = boto3.client('s3')

    pager = client.get_paginator("list_objects_v2")

    logging.info(f"Searching {bucket}...")
    for page in pager.paginate(Bucket=bucket):
        remote_contents = page['Contents']
        for key in remote_contents:
            all_object_keys.append(key['Key'])

    logging.info(f"Bucket {bucket} contains {len(all_object_keys)} objects.")

    return all_object_keys

def load_previous_manifest(bucket: str, manifest_name: str):
    """Loads a manifest yaml from the bucket.
    This has two main purposes:
    1. To avoid validating old builds
    2. To keep previous records, even if they don't exist
        on the bucket anymore
    :param bucket: name of the bucket
    :param manifest_name: name of the manifest file
    :return: list of GraphDataPackage and DataResource objects with their values
    """

    client = boto3.client('s3')
    old_manifest_name = manifest_name+".old"
    logging.info(f"Retrieving {manifest_name} from {bucket}...")
    client.download_file(bucket,manifest_name,old_manifest_name)

    previous_objects = []

    # Set LinkML global strict to False
    # as we can't ensure everything is a valid CURIE
    strictness.lax()

    # Parse the yaml
    with open(old_manifest_name) as infile:
        yaml_parsed = yaml.safe_load(infile)

    # Now load entries as objects
    for entry in yaml_parsed:
        if "compression" in entry:
            data_object = GraphDataPackage(**entry)
        else:
            data_object = DataResource(**entry)
        previous_objects.append(data_object)

    logging.info(f"Loaded {len(previous_objects)} entries from previous Manifest.")

    return previous_objects

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

def validate_merged_graph(bucket, graph_key):
    """Given a string for a remote key to a tar.gz
    graph file expected to contain one node list
    and one edge list, both in KGX format,
    validates accordingly.
    Downloads the graph files locally to do so.
    The full KGX validation can take a long time, 
    especially if there are many validation errors,
    so it may not be appropriate to perform
    for all graphs. 
    :param bucket: name of S3 bucket, needed to retrieve graph files
    :param graph_key: str, the remote key for the graph file
    :return: dict of bools
    """

    results = {"file count correct": False,
                "file names correct": False,
                "no KGX validation errors": False}

    temp_dir = 'data'
    log_dir = 'logs'
    project_name = (graph_key.split("/"))[0]
    build_name = (graph_key.split("/"))[1]
    temp_path = os.path.join(temp_dir,'temp_graph.tar.gz')
    log_path = os.path.join(log_dir,f'kgx_validate_{project_name}_{build_name}.log')

    client = boto3.client('s3')

    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    logging.info(f"Retrieving {graph_key}...")
    client.download_file(bucket, graph_key, temp_path)
    with tarfile.open(temp_path) as graph_file:
        contents = graph_file.getnames()
        if len(contents) > 2:
            logging.warning(f"Found >2 files in graph from {graph_key}.")
            shutil.rmtree(temp_dir)
            return results
        else:
            results["file count correct"] = True
        if not 'merged-kg_edges.tsv' in contents \
            and 'merged-kg_nodes.tsv' in contents:
            logging.warning(f"Unexpected node/edge file names: {contents}")
        else:
            results["file names correct"] = True

        # Verify that it's OK to proceed
        full_validation = True
        if project_name in VALIDATION_DENYLIST:
            full_validation = False
            logging.info("Not performing full validation with KGX.")

        if full_validation:
            logging.info("Validating graph files with KGX...")
            
            try:
                errors = kgx.cli.validate(inputs=[temp_path],
                            input_format="tsv",
                            input_compression="tar.gz",
                            output=log_path,
                            stream=False)
                if len(errors) > 0: # i.e. there are any real errors
                    logging.warning(f"KGX found errors in graph files. See {log_path}")
                else:
                    results["no KGX validation errors"] = True
            except TypeError as e:
                logging.error(f"Error while validating: {e}")

    # Clean up
    shutil.rmtree(temp_dir)

    return results

def validate_projects(bucket: str, keys: list, graph_file_keys: dict) -> None:
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
    :param bucket: name of S3 bucket, needed to retrieve graph files
    :param keys: list of object keys, as strings
    :param graph_file_keys: dict of keys appearing to be graph files,
                            with two lists with the keys
                            "compressed" and "uncompressed",
                            respectively
    :return: dict, project_contents with keys as project names, 
                values are dicts
    """

    project_contents = {}

    # Check which projects/builds the graph keys are in first,
    # so we don't bother with those without updates
    graph_file_key_projects = []
    graph_file_key_builds = []
    for object_type in graph_file_keys:
        for keyname in graph_file_keys[object_type]:
            graph_file_key_projects.append((keyname.split("/"))[0])
            graph_file_key_builds.append((keyname.split("/"))[1])
    # Just the unique project names
    graph_file_key_projects = list(set(graph_file_key_projects)) 

    # Iterate through all keys for each project,
    # then go back and iterate through individual builds only
    # to validate
    for project_name in PROJECTS:
        if project_name == "kg-obo": 
            continue # Don't validate KG-OBO, it has its own validators
        if project_name not in graph_file_key_projects:
            logging.info(f"No updates for {project_name}.")
            continue # No updates
        project_contents[project_name] = {"objects":[],
                                            "builds": [],
                                            "valid builds":[],
                                            "incorrectly named builds":[],
                                            "incorrectly structured builds":[],
                                            "builds with issues in tar.gz":[]}
        logging.info(f"Validating new builds for {project_name}...")
        for keyname in keys:
            try:
                project_dirname = (keyname.split("/"))[0]
                if project_dirname == project_name: # This is the target project
                    project_contents[project_name]["objects"].append(keyname)

                    # Now collect all new builds
                    build_name = (keyname.split("/"))[1]
                    if build_name not in project_contents[project_name]["builds"] and \
                        build_name not in ["index.html", "current","README"]:
                        project_contents[project_name]["builds"].append(build_name)

            except IndexError:
                pass
        
        # Iterate through builds now to validate
        for build_name in project_contents[project_name]["builds"]:
            
            # Just the new ones
            if build_name not in graph_file_key_builds:
                continue # No updates

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

            # Find the corresponding merged KG
            merged_graph_key = ""
            for graph_key in graph_file_keys["compressed"]:
                if (graph_key.split("/"))[0] == project_name and (graph_key.split("/"))[1] == build_name:
                    merged_graph_key = graph_key
                    break
            if merged_graph_key == "": # We don't even have a graph file for this build
                valid = False
            else:
                graph_validation_results = validate_merged_graph(bucket, merged_graph_key)
                if not graph_validation_results["file count correct"] or \
                    not graph_validation_results["file names correct"]:
                    valid = False
                    project_contents[project_name]["builds with issues in tar.gz"].append(build_name)
                if not graph_validation_results["no KGX validation errors"]: # almost never happens
                    logging.info(f"Build in {merged_graph_key} may contain format errors.")

            if valid:
                project_contents[project_name]["valid builds"].append(build_name)

        logging.info(f"The project {project_name} contains:")
        for object_type in project_contents[project_name]:
            object_count = len(project_contents[project_name][object_type])
            if object_count > 0:
                logging.info(f"\t{object_count} {object_type}")
                if object_type in ["incorrectly named builds",
                                    "incorrectly structured builds",
                                    "builds with issues in tar.gz"]:
                    invalid_builds = project_contents[project_name][object_type]
                    logging.info(f"\t\t{invalid_builds}")
        
    return project_contents

def get_graph_file_keys(keys: list, maximum: int, previous_manifest = []):
    """Given a list of keys, returns a list of those
    resembling graphs.
    If passed a previous_manifest, will ignore the keys
    for all object ids so we don't validate them
    redundantly in subsequent steps.
    :param keys: list of object keys, as strings
    :param previous_manifest: list of parsed manifest objects
                                object.id is full url
    :return: dict of all keys appearing to be graph files,
            with keys denoting `compressed` or `uncompressed`.
            Values are lists of strings."""
    
    graph_file_keys = {"compressed":[],"uncompressed":[]}

    # Prep the list of keys from previous_manifest
    previous_manifest_keys = []
    for object in previous_manifest:
        previous_manifest_keys.append(object.id)

    for keyname in keys:
        url = "https://kg-hub.berkeleybop.io/" + keyname
        if url in previous_manifest_keys:
            continue
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
        logging.info(f"Found {len(graph_file_keys[object_type])} new {object_type} graph files.")

    if maximum:
        logging.info(f"Will consider only {maximum} files in total.")
        graph_file_keys["compressed"] = (graph_file_keys["compressed"])[:maximum]
        remaining = maximum - len(graph_file_keys["compressed"])
        if remaining > 0:
            graph_file_keys["uncompressed"] = (graph_file_keys["uncompressed"])[:remaining]
        else:
            graph_file_keys["uncompressed"] = []
        
        for object_type in graph_file_keys:
            logging.info(f"Will process {len(graph_file_keys[object_type])} new {object_type} graph files.")

    return graph_file_keys

def create_dataset_objects(objects: list, project_metadata: dict, project_contents: dict,
                            previous_manifest = []):
    """Given a list of object keys, returns a list of
    LinkML-defined GraphDataPackage objects.
    See datasets.py for class definitions.
    :param objects: list of object keys
    :param project_metadata: dict of parsed metadata for specific projects,
                            with project names as keys
    :param project_contents: dict with keys as project names values are dicts
    :param previous_manifest: list of objects we have previously written to Manifest
    :return: list of GraphDataPackage and DataResource objects with their values"""

    all_data_objects = []

    # Append previous entries first
    for data_object in previous_manifest:
        all_data_objects.append(data_object)

    for object_type in objects:
        for object in objects[object_type]:
            url = "https://kg-hub.berkeleybop.io/" + object
            title = (object.split("/"))[-1]
            project_name = (object.split("/"))[0]
            build_name = (object.split("/"))[1]
      
            if object_type == "compressed":
                data_object = GraphDataPackage(id=url,
                                    title=title,
                                    compression="tar.gz",
                                    resources=['merged-kg_edges.tsv', 'merged-kg_nodes.tsv'])
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

def get_stats(bucket: str, data_objects: list):
    """Given a list of LinkML-defined dataset objects,
    attempts to retrieve KGX stats about each graph.
    Only considers compressed graphs.
    :param bucket: name of the bucket
    :param data_objects: list of GraphDataPackage and DataResource objects
    :return: list of GraphDataPackage and DataResource objects with their values
    """

    new_data_objects = []

    for object in data_objects:
        object_key = ((object.id).split("https://kg-hub.berkeleybop.io"))[1]
        object_project = (object_key.split("/"))[1]
        object_type = (object_key.split("/"))[3]
        if object.compression == "tar.gz" and object_project != "kg-obo" \
            and object_type not in ["raw", "transformed"]:
            stats = retrieve_stats(bucket, object_key)
            if stats:
                object.edge_count = stats['edge_stats']['total_edges']
                object.node_count = stats['node_stats']['total_nodes']

                try:
                    object.predicates = "|".join(stats['edge_stats']['predicates'])
                except KeyError: # at one point this was called edge_labels
                    object.predicates = "|".join(stats['edge_stats']['edge_labels'])

                object.node_categories = "|".join(stats['node_stats']['node_categories'])

                try:
                    object.node_prefixes = "|".join(stats['node_stats']['node_id_prefixes'])
                except KeyError: # may not be present
                    pass

    new_data_objects = data_objects

    return new_data_objects 

def check_urls(bucket: str, data_objects: list):
    """Given a list of LinkML-defined dataset objects,
    checks the id of each to see if it resolves to an
    object on the remote.
    If not, the object is marked as obsolete.
    (All keys are checked, and if a link somehow becomes
    unbroken, it will be un-set as obsolete.)
    :param bucket: name of the bucket
    :param data_objects: list of GraphDataPackage and DataResource objects
    :return: list of GraphDataPackage and DataResource objects with their values
    """

    client = boto3.client('s3')

    new_data_objects = []

    for object in data_objects:
        object_key = ((object.id).split("https://kg-hub.berkeleybop.io/"))[1]
        try:
            client.head_object(Bucket=bucket, Key=object_key)
            object.obsolete = "False"
        except botocore.errorfactory.ClientError:
            object.obsolete = "True"
            logging.warning(f"!!! {object_key} not found in bucket. Marking as obsolete.")
        new_data_objects.append(object)

    return new_data_objects

def write_manifest(data_objects: list, outpath: str) -> None:
    """Given a list of LinkML-defined dataset objects,
    dumps them to a YAML file.
    If this file already exists, it is overwritten.
    :param data_objects: list of GraphDataPackage and DataResource objects
    :param outpath: str, filename or path to write to
    """
    
    header = "# Manifest for KG-Hub graphs\n"

    with open(outpath, 'w') as outfile:
        outfile.write(header)
        outfile.write(yaml_dumper.dumps(data_objects))

    logging.info(f"Wrote to {outpath}.")

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
        logging.info(f"Loading OBO metadata from cached {onto_file_name}...")
        with open(onto_file_name) as infile:
            yaml_parsed = yaml.safe_load(infile)
            yaml_onto_list: list = yaml_parsed['ontologies']

    else: # Retrieve and save
        logging.info(f"Retrieving OBO metadata from {yaml_url}...")

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
