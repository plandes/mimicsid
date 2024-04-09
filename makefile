## makefile automates the build and deployment for python projects


## Build system
#
# build config
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy markdown

# build
ADD_CLEAN +=		$(shell find example -type d -name __pycache__)
ADD_CLEAN +=		preds
CLEAN_ALL_DEPS +=	data-clean
PY_DEP_POST_DEPS +=	modeldeps

# project specific
DIST_BIN =		./dist
MODEL =			glove300
SID_ARGS = 		-c config/$(MODEL).conf

PY_SRC_TEST_PAT ?=	'test_parse.py'


## Includes
#
include ./zenbuild/main.mk


## Targets
#
# install dependencies need by the the models (both training and inference)
.PHONY:			modeldeps
modeldeps:
			$(PIP_BIN) install $(PIP_ARGS) \
				-r $(PY_SRC)/requirements-model.txt --no-deps

# test for successful training per the code by limiting epochs and batch size
.PHONY:			trainfast
trainfast:
			if [ ! -d data/shared/adm ] ; then \
				$(DIST_BIN) preempt $(SID_ARGS) -w 1 ; \
			fi
			$(DIST_BIN) traintest $(SID_ARGS) -p --override \
			  'model_settings.epochs=2,batch_stash.batch_limit=3'

# train production models
.PHONY:			preprocess
preprocess:
			@echo "expecting passwords set in config/system.conf..."
			nohup ./src/bin/preprocess.sh > preprocess.log 2>&1 &
			@echo "remember to remove passwords in config/system.conf after complete"

# train production models and then package them in a staging directory
.PHONY:			packageprod
packageprod:
			@echo "remember to remove passwords in config/system.conf"
			nohup ./src/bin/package.sh > package.log 2>&1 &

# stop any training
.PHONY:			stop
stop:
			mkdir -p data/model/model
			touch data/model/model/update.json

# stop training by killing processes
.PHONY:			hardstop
hardstop:
			ps -eaf | grep python | grep $(DIST_BIN) | \
				grep -v grep | awk '{print $$2}' | xargs kill

# test parsing
.PHONY:			testparse
testparse:
			$(eval cor=17)
			@$(DIST_BIN) predict \
			  --config config/glove300.conf \
			  --path - test-resources/note.txt | \
			  wc -l | xargs -i{} bash -c \
			  "if [ '{}' != '$(cor)' ] ; then echo {} != $(cor) ; exit 1 ; fi"
			@echo "success: line count output: $(cor)"

# test the MIMIC-III database (unavilable database in GitHub workflows)
.PHONY:			testdb
testdb:
			make PY_SRC_TEST=test/db test

# test prediction and the DB access
.PHONY:			testall
testall:		test testparse testdb

.PHONY:			data-clean
data-clean:		clean
			rm -f *.log
			rm -fr data
			make -C docker/app cleanall
