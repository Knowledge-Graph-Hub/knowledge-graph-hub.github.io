# make_kg_manifest.py

"""Utility for generating KG-Hub Manifest file,
containing a list of all graphs and subgraphs
(i.e., full KGs and graphs of transformed sources)
for all KG-Hub projects.
The Manifest file follows the LinkML Datasets
schema as defined here:
https://github.com/linkml/linkml-model/blob/main/linkml_model/model/schema/datasets.yaml
Objects have unique IDs that are URLs."""

import boto3
import botocore.exceptions
import botocore.errorfactory
import click

from linkml_runtime.dumpers import yaml_dumper

#LinkML class
import datasets
from datasets import DataPackage

@click.command()
@click.option("--bucket",
               required=True,
               nargs=1,
               help="""The name of an AWS S3 bucket to generate Manifest for.""")
def run(bucket: str):
    try:
        keys = list_bucket_contents(bucket)
        graph_file_keys = get_graph_file_keys(keys)
        dataset_objects = create_dataset_objects(graph_file_keys)
        write_manifest(dataset_objects)
    except botocore.exceptions.NoCredentialsError:
        print("Can't find AWS credentials.")

def list_bucket_contents(bucket: str):
    """Lists all contents, keys only, of an AWS S3 bucket.
    :param bucket: name of the bucket
    :return: list of all keys, as strings, in the bucket"""
    
    all_object_keys = []

    client = boto3.client('s3')

    pager = client.get_paginator("list_objects_v2")

    print(f"Searching {bucket}...")
    for page in pager.paginate(Bucket=bucket):
        remote_contents = page['Contents']
        for key in remote_contents:
            all_object_keys.append(key['Key'])

    print(f"Bucket {bucket} contains {len(all_object_keys)} objects.")

    return all_object_keys

def get_graph_file_keys(keys: dict):
    """Given a list of keys, returns a list of those
    resembling graphs.
    :param keys: list of object keys, as strings
    :return: dict of all keys appearing to be graph files,
            with keys denoting `compressed` or `uncompressed`.
            Values are lists of strings."""
    
    graph_file_keys = {"compressed":[],"uncompressed":[]}

    for keyname in keys:
        if keyname[-7:] == ".tar.gz":
            graph_file_keys["compressed"].append(keyname)
        if keyname[-9:] in ["edges.tsv", "nodes.tsv"]:
            graph_file_keys["uncompressed"].append(keyname)

    for object_type in graph_file_keys:
        print(f"Found {len(graph_file_keys[object_type])} {object_type} graph files.")

    return graph_file_keys

def create_dataset_objects(objects: list):
    """Given a list of object keys, returns a list of
    LinkML-defined DataPackage objects.
    See datasets.py for class definitions.
    :param objects: list of object keys
    :return: list of DataPackage objects with their values"""

    #TODO: assign description and was_derived_from to objects
    #       This may need to be extracted on a per-project basis
    #TODO: get version for projects other than KG-OBO
    #TODO: consider using other LinkML class for uncompressed files

    all_packages = []

    for object_type in objects:
        for object in objects[object_type]:
            url = "https://kg-hub.berkeleybop.io/" + object
            title = (object.split("/"))[-1]
      
            package = DataPackage(id=url,
                                    title=title,
                                    language="EN")
            if object_type == "compressed":
                DataPackage.compression = "tar.gz"
            if (object.split("/"))[0] == "kg-obo":
                DataPackage.version = (object.split("/"))[-2]
            all_packages.append(package)

    return all_packages

def write_manifest(data_objects: list) -> None:
    """Given a list of LinkML-defined DataPackage objects,
    dumps them to a YAML file.
    :param data_objects: list of DataPackage objects
    :return
    """
    outpath = "MANIFEST.yaml"

    with open(outpath, 'w') as outfile:
        outfile.write("# Manifest for KG-Hub graphs\n")
        outfile.write(yaml_dumper.dumps(data_objects))

    print(f"Wrote to {outpath}.")

if __name__ == '__main__':
  run()