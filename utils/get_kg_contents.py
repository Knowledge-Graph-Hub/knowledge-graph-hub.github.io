# get_kg_contents.py

"""
Helper functions for retrieving details from KG-Hub
projects, including:
* Graph data sources
* CURIE namespaces
* Biolink types
If possible, these are parsed from KGX stats output.
"""

import boto3
import yaml

def retrieve_stats(bucket: str, graph_key: str):
    """
    Given a key to a graph file,
    searches for the accompanying KGX
    stats output (usually in
    /stats/merged_graph_stats.yaml 
    of the build directory).
    :param bucket: str, name of the bucket
    :param key: str, full key for graph file
                usually <kg-name>.tar.gz
    :return: dict of parsed stats file
    """

    stats = {}
    stats_keys = []
    local_stats_filename = "stats.yaml"

    stats_dir = ("/".join((graph_key.split("/"))[:-1]) + "/stats/")[1:]

    client = boto3.client('s3')

    # Check if we have a stats yaml
    print(f"Searching for stats file in {stats_dir}...")
    stats_key = ""
    stats_files = client.list_objects_v2(Bucket=bucket, Prefix=stats_dir)
    if stats_files['KeyCount'] == 0:
        print(f"Found no stats file for {graph_key}.")
        return stats
    for key in stats_files['Contents']:
        stats_keys.append(key['Key'])
    for key in stats_keys:
        if (key.split("/"))[-1] == "merged_graph_stats.yaml":
            print(f"Found graph stats in {key}.")
            stats_key = key
            break
        elif ".yaml" in (key.split("/"))[-1]:
            print(f"Found possible graph stats in {key}...")
            stats_key = key
            break
    if stats_key == "":
        print(f"Found no stats file for {graph_key}.")
        return stats

    # Download stats file and parse
    print(f"Retrieving {stats_key}")
    client.download_file(bucket,stats_key,local_stats_filename)

    with open(local_stats_filename) as infile:
        yaml_parsed = yaml.safe_load(infile)

    stats = yaml_parsed

    return stats
        

