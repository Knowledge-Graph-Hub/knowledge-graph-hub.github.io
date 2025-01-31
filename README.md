# Knowledge Graph Hub: Web Site and Metadata Generation

This repository contains the code for assembling the Knowledge Graph Hub (KG-Hub) web site.

The site contains documentation for the KG-Hub project.

See below for details on the Knowledge Graph Registry (KG-Registry).

Visit the site at <https://kghub.org/>.

## Registry

The KG-Hub site also hosts the KG-Registry.

The site it at <https://kghub.org/kg-registry/>.

The repository for the registry is at <https://github.com/Knowledge-Graph-Hub/kg-registry>.

To request addition of a new KG project to the registry, please [open an issue here](https://github.com/Knowledge-Graph-Hub/kg-registry/issues/new?template=new-resource.yml).

## For Developers

This project uses `poetry`. After cloning the repository, it may be installed by running `poetry install` from its root directory.

The `utils` directory contains utilities for tracking metadata on all graphs on KG-Hub, with the major KG projects listed in `projects.yaml`.

Graph collections are modeled using [LinkML](https://github.com/linkml/linkml). See `utils/models/` for more details.

## License

Projects and resources mentioned on KG-Hub or the KG-Registry may vary in code and data licensing.

Please consult documentation for each resource regarding reuse.
