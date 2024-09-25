# Knowledge Graph Hub: Web Site and Metadata Generation

This repository contains the code for assembling the Knowledge Graph Hub (KG-Hub) web site.

Visit the site at <https://kghub.org/>.

## For Developers

This project uses `poetry`. After cloning the repository, it may be installed by running `poetry install` from its root directory.

To build the site, do the following:

* Install [Poetry](https://python-poetry.org/) if needed.
* Clone the repository
* Change to the root directory of the cloned repo, then run `poetry install`.
* Change to the `docs` directory and run `build_site.sh`. This will retrieve recent metadata.
* Run `mkdocs gh-deploy` to deploy the site.

## Updates

To request addition of a new KG project to this site, please do one of the following:

1. Open an issue on the [Knowledge Graph Hub Support Repository](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub-support).
2. Open a pull request on this repository to add the new project details to [this file](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub.github.io/blob/master/utils/projects.yaml).
