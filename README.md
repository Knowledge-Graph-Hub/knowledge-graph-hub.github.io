# Knowledge Graph Hub

The purpose of Knowledge Graph Hub (KG Hub) is to provide a platform for building knowledge graphs (KGs) by adopting a set of guidelines and design principles.

The goal of KG Hub is to serve as a collective resource to simplify the process of generating biological and biomedical KGs and thus reducing the barrier for entry to new participants.

In a KG Hub, each independent effort for building a KG is an instance of the KG Hub.

For example, [KG-COVID-19](https://github.com/Knowledge-Graph-Hub/kg-covid-19), a light-weight ETL framework for building a COVID-19 KG, is an instance of KG Hub.


## Design principles

- Each instance of KG Hub,
    - should live in its own GitHub repository within the [Knowledge-Graph-Hub](https://github.com/Knowledge-Graph-Hub/) organization.
    - should have code and/or configurations for Extract, Transform, and Load (ETL) and must be reproducible.
    - should do their best to model their data using the Biolink Model, where possible.
    - should make use of ontologies from the [OBOFoundry](http://www.obofoundry.org/), where possible.
    - should be responsible for the veracity of the datasets that they ingest and are responsible for keeping track of evidence and provenance for assertions in their KG.
    - should provide their KG for download and must follow [semantic versioning guidelines](https://semver.org/).
    - should provide their KG in the [KGX interchange format](https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md) in addition to their format of choice.
    - must have a License, Contributing guidelines, Code of Conduct, and be open to the community for contributions as well as consumption.


- Optionally, each instance of a KG Hub can also provide,
    - a Docker image such that their code can be run easily as a container.



