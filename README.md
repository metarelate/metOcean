metOcean
=========

metOcean mapping is a knowledge repository providing information on translating meteorological and oceanographic metadata.

The knowledge is stored as RDF Turtle datasets in StaticData, modelled using the Metarelate terminology mapping model.

To contribute to the project, the static data should be used to populate a local triple store which an instance of the metarelate management software may access. 

Dependencies
------------
* metarelate - https://github.com/metarelate/metarelate

To use this repository with metarelate, set your local environment variables:

* METARELATE_STATIC_DIR='/path/to/your/working/copy/of/metOcean/staticData/'
* METARELATE_TDB_DIR='/a/path/to/a/writeable/folder/for/a/local/triplestore'
* METARELATE_DATA_PROJECT='metOcean' 
