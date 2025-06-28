#@meta {desc: "Python build configuration", date: "2025-06-26"}


## Build system
#
# build config
PROJ_TYPE =		python
PROJ_MODULES =		python/doc python/package python/deploy
PY_TEST_TARGETS =	testcur
PY_TEST_ALL_TARGETS +=	testparse
ADD_CLEAN +=		preds
CLEAN_ALL_DEPS +=	data-clean
PY_DEP_POST_DEPS +=	modeldeps


## Project specific
#
PRED_BIN =		./harness.py
DIST_BIN =		./dist
MODEL =			glove300
SID_ARGS = 		-c config/$(MODEL).conf
ENV_FILE =		environment.yml


## Includes
#
include ./zenbuild/main.mk


## Targets
#
# test for successful training per the code by limiting epochs and batch size
.PHONY:			trainfast
trainfast:
			@echo "deleting stale data"
			if [ ! -d data/shared/adm ] ; then \
				$(DIST_BIN) preempt $(SID_ARGS) -w 1 ; \
			fi
			@echo "training model for 2 epochs..."
			$(MAKE) $(PY_MAKE_ARGS) pyharn \
				PY_HARNESS_BIN=$(DIST_BIN) \
				ARG="traintest $(SID_ARGS) -p --override \
				'model_settings.epochs=2,batch_stash.batch_limit=3'"

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

# update the tracked conda environment file
$(ENV_FILE):		$(PY_CONDA_ENV_FILE)
			@echo "updating $(ENV_FILE)"
			@$(MAKE) $(PY_MAKE_ARGS) $(PY_CONDA_ENV_FILE)
			@cp $(PY_CONDA_ENV_FILE) $(ENV_FILE)
			@sed -i 's/name: \(.*\)/name: mimicsid/' $(ENV_FILE)
			@echo "created $(ENV_FILE)"

# recreate the environment file
.PHONY:			envfile
envfile:
			@echo "recreating the the environment file..."
			@rm -f $(ENV_FILE)
			@$(MAKE) $(PY_MAKE_ARGS) $(ENV_FILE)


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

# test parsing
.PHONY:			testparse
testparse:
			@echo "testing parsing..."
			@$(MAKE) $(PY_MAKE_ARGS) pyharn \
			  PY_INVOKE_ARG="-e testcur " \
			  ARG="predict --config config/glove300.conf \
				--path - test-resources/note.txt" | \
			diff - test-resources/should-predict.txt || \
			  exit 1
			@echo "testing parsing...ok"

# test prediction and the DB access
.PHONY:			data-clean
data-clean:
			@echo "removing mimicsid logs, ./data, docker"
			@rm -f *.log
			@rm -fr data
			@$(MAKE) -C docker/app cleanall
