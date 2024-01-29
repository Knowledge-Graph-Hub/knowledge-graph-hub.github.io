# Knowledge Graph Hub: Web Site and Metadata Generation

This repository contains the code for assembling the Knowledge Graph Hub (KG-Hub) web site.

Visit the site at <https://kghub.org/>.

The `utils` directory contains utilities for tracking metadata on all graphs on KG-Hub, with the major KG projects listed in `projects.yaml`.

Graph collections are modeled using [LinkML](https://github.com/linkml/linkml). See `utils/models/` for more details.

## Updates

To request addition of a new KG project to this site, please do one of the following:

1. Open an issue on the [Knowledge Graph Hub Support Repository](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub-support).
2. Open a pull request on this repository to add the new project details to [this file](https://github.com/Knowledge-Graph-Hub/knowledge-graph-hub.github.io/blob/master/utils/projects.yaml).
