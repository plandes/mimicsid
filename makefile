## makefile automates the build and deployment for python projects


## Build system
#
# build config
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy markdown

# build
ADD_CLEAN +=		$(shell find example -type d -name __pycache__)
CLEAN_ALL_DEPS +=	data-clean
PY_DEP_POST_DEPS +=	modeldeps

# project specific
ENTRY =			./mimicsid
MODEL =			glove300
SID_ARGS = 		-c models/$(MODEL).conf


## Includes
#
include ./zenbuild/main.mk


## Targets
#
# install dependencies need by the the models (both training and inference)
.PHONY:			modeldeps
modeldeps:
			$(PIP_BIN) install $(PIP_ARGS) -r $(PY_SRC)/requirements-model.txt --no-deps

# test for successful training per the code by limiting epochs and batch size
.PHONY:			trainfast
trainfast:
			$(ENTRY) traintest $(SID_ARGS) -p --override \
			  'model_settings.epochs=2,batch_stash.batch_limit=3'

# recreate batches
.PHONY:			recreatebatch
recreatebatch:
			rm -rf target model data
			$(ENTRY) batch -c etc/batch.conf

# stop any training
.PHONY:			stop
stop:
			mkdir -p data/model/model
			touch data/model/model/update.json

# stop training by killing processes
.PHONY:			hardstop
hardstop:
			ps -eaf | grep python | grep $(ENTRY) | \
				grep -v grep | awk '{print $$2}' | xargs kill

# test the MIMIC-III database (unavilable database in GitHub workflows)
.PHONY:			testdb
testdb:
			make PY_SRC_TEST=test/db test

# test prediction and the DB access
.PHONY:			testall
testall:		test testdb

.PHONY:			data-clean
data-clean:		clean
			rm -f *.log
			make -C docker/app cleanall
