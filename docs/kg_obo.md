# KG-OBO
  
KG-OBO translates the biological and biomedical ontologies on [OBO Foundry](https://obofoundry.org/) into graph nodes and edges.

- [See all KG-OBO graphs](https://kghub.io/kg-obo/)
- [Visit the KG-OBO GitHub repository](https://github.com/Knowledge-Graph-Hub/kg-obo)

## What is KG-OBO?

Knowledge graphs, or KGs, are powerful tools for modeling and learning from the complex relationships being constantly discovered among biological and biomedical phenomena.

Though it can be useful to assemble a set of interactions alone (e.g., between proteins, genes, and even diseases or their symptoms), a complete understanding of these associations may be difficult to acquire without comprehensive domain knowledge.

This is where ontologies can help.
Each ontology defines the relationships between concepts, often in hierarchies.
If you need to know whether salicylsulfuric acid and fenpicoxamid have anything in common (they're both esters, at least), the [CHEBI](https://obofoundry.org/ontology/chebi.html) ontology can help.
If you're trying to model the relationships between the cephalopod *Enoploteuthis leptura* and other species, there's [an ontology](https://obofoundry.org/ontology/ceph.html) for that too.

Ontologies are carefully designed to define specific relationships and their internal formats reflect this purpose.
These formats (often OWL or OBO) are not naturally compatible with knowledge graph assembly.
Their classes require translation into nodes and their relationships must be translated into edges, all with a single, consistent format retaining as much of the original ontology's value as possible.
It's also preferable to keep track of which version of each ontology is to be used in a KG, for the sake of reproducibility.

KG-OBO takes care of this for you.

## Ontology Graphs in KG-OBO

The table below lists all graphs on KG-OBO, including both current and previous versions of ontologies.

Clicking the link for "Current KG Version" will take you directly to the compressed graph file.

<div class="col-md-12">
  <div class="row">
  <div class="col-md-12">
    {% include kgobo_table.html %}
  </div>
  </div>
</div>
