# KG-Hub

A collection of biological and biomedical Knowledge Graphs, including their component data sources.

## Learn more about KG-Hub

- [See the list of core graphs we maintain](https://kghub.io/MANIFEST.yaml)
- [See the KG-Registry](https://kghub.org/kg-registry/)
- [Browse all publicly available files stored on KG-Hub](https://kghub.io/)
- [View the KG-Hub Dashboard](http://kghub.org/kg-hub-dashboard/)

## Build your own KG

- [Get started (from scratch)](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub-support/blob/main/kg-hub-tutorials/KG-Hub%20Tutorial%201%20-%20Getting%20Started.ipynb)
- [Get help from the community](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub-support)
- [Try machine learning on KGs](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub-support/blob/main/kg-hub-tutorials/KG-Hub%20Tutorial%203%20-%20Link%20Prediction%20and%20More%20Graph%20Machine%20Learning.ipynb)

## Purpose

The purpose of Knowledge Graph Hub (KG-Hub) is to provide a platform for building knowledge graphs (KGs) by adopting a set of guidelines and design principles.

The goal of KG-Hub is to serve as a collective resource to simplify the process of generating biological and biomedical KGs and thus reducing the barrier for entry to new participants.

KG-Hub also maintains:

- Tools for building your own KGs
- Code for building specific "core" KGs
  - For example, [KG-COVID-19](https://github.com/Knowledge-Graph-Hub/kg-covid-19)
- The products of "core" KGs, in a convenient exchange format (KGX)
- A set of OBO ontologies as graph nodes and edges
  - See [KG-OBO](https://kghub.org/kg_obo/)
- A registry of our own and community-developed KGs and related data sources
  - See [KG-Registry](https://kghub.org/kg-registry/)

## Design Principles

- Each core instance of KG-Hub,
  - should live in its own GitHub repository within the [Knowledge-Graph-Hub](https://github.com/Knowledge-Graph-Hub/) organization.
  - should have code and/or configurations for Extract, Transform, and Load (ETL) and must be reproducible.
  - should do their best to model their data using the Biolink Model, where possible.
  - should make use of ontologies from the [OBO Foundry](http://www.obofoundry.org/), where possible.
  - should be responsible for the veracity of the datasets that they ingest and are responsible for keeping track of evidence and provenance for assertions in their KG.
  - should provide their KG for download and must follow [semantic versioning guidelines](https://semver.org/).
  - should provide their KG in the [KGX interchange format](https://github.com/biolink/kgx/blob/master/docs/data-preparation.md) in addition to their format of choice.
  - must have a License, Contributing guidelines, Code of Conduct, and be open to the community for contributions as well as consumption.

Optionally, each instance of KG-Hub can also provide a Docker image such that their code can be run easily as a container.

## Core KG-Hub Projects

The table below lists core KG projects. Click headings to sort.

{{ read_yaml('projects.yaml') }}
