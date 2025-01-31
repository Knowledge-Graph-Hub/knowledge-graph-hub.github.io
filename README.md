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

To build the site, do the following:

* Install [Poetry](https://python-poetry.org/) if needed.
* Clone the repository
* Change to the root directory of the cloned repo, then run `poetry install`.
* Change to the `docs` directory and run `build_site.sh`. This will retrieve recent metadata.
* Run `mkdocs gh-deploy` to deploy the site.

## License

Projects and resources mentioned on KG-Hub or the KG-Registry may vary in code and data licensing.

Please consult documentation for each resource regarding reuse.
