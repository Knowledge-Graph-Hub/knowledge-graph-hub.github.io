# make_kg_manifest.py

"""Utility for generating KG-Hub Manifest file,
containing a list of all graphs and subgraphs
(i.e., full KGs and graphs of transformed sources)
for all KG-Hub projects.
The Manifest file follows the LinkML Datasets
schema as defined here:
https://github.com/linkml/linkml-model/blob/main/linkml_model/model/schema/datasets.yaml"""

import boto3
import botocore.exceptions
import botocore.errorfactory
import click

@click.command()
@click.option("--bucket",
               required=True,
               nargs=1,
               help="""The name of an AWS S3 bucket to generate Manifest for.""")
def run(bucket: str):
    try:
        keys = list_bucket_contents(bucket)
        graph_file_keys = get_graph_file_keys(keys)
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

def get_graph_file_keys(keys: list):
    """Given a list of keys, returns a list of those
    resembling graphs.
    :param keys: list of object keys, as strings
    :return: dict of all keys appearing to be graph files,
            with keys denoting `compressed` or `uncompressed`.
            Values are lists of strings."""
    
    graph_file_keys = {"Compressed":[],"Uncompressed":[]}

    for keyname in keys:
        if keyname[-7:] == ".tar.gz":
            graph_file_keys["Compressed"].append(keyname)
        if keyname[-9:] in ["edges.tsv", "nodes.tsv"]:
            graph_file_keys["Uncompressed"].append(keyname)

    print(graph_file_keys)

    return graph_file_keys

if __name__ == '__main__':
  run()