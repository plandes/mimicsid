# Docker image

This repository contains a docker image for the [MedSecId] project, which
contains annotations for sections of clinical notes, such as electronic health
care (EHR) medical documents.  It also comes with a model to automatically
section notes.

If all you want is the [mednlp] tooling or predicting sections using [mednlp],
you can clone this repository and comment out the [mimicdb] section.  However,
if you want to access MIMIC-III data, follow the instructions on how to obtain
or build the database from the [mimicdb] repository.


## Usage

The [makefile](makefile) controls building of the image and its life cycle.  To
build the image from scratch:

1. Remove any previous Docker image: `make dockerrm`
1. Clean any previous derived objects: `make cleanall`
1. Build the image: `make build`
1. Start the image(s): `make up`


## Obtaining

The [Docker image](https://hub.docker.com/repository/docker/plandes/mimicsid)
can be installed with:
```bash
docker pull plandes/mimicsid:latest
```



<!-- links -->
[mimicdb]: https://github.com/plandes/mimicdb
[mednlp]: https://github.com/plandes/mednlp
[mimic]: https://github.com/plandes/mimic
[MedSecId]: https://github.com/plandes/mimicsid
