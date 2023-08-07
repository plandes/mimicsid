## makefile automates the build and deployment for python projects

PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy markdown
ADD_CLEAN +=		$(shell find example -type d -name __pycache__)
CLEAN_ALL_DEPS +=	data-clean
PIP_ARGS +=		--use-deprecated=legacy-resolver
PY_DEP_POST_DEPS +=	modeldeps
ENTRY =			./mimicsid
MODEL =			glove300
SID_ARGS = 		-c models/$(MODEL).conf
HEADER_ARGS =		$(SID_ARGS) --override mimicsid_default.model_type=header,model_settings.epochs=20
TRAIN_LOG = 		train.log

include ./zenbuild/main.mk

.PHONY:			modeldeps
modeldeps:
			$(PIP_BIN) install $(PIP_ARGS) -r $(PY_SRC)/requirements-model.txt --no-deps

.PHONY:			testdb
testdb:
			make PY_SRC_TEST=test/db test

.PHONY:			testall
testall:		test testdb

.PHONY:			traintest
traintest:
			nohup $(ENTRY) traintest $(SID_ARGS) > $(TRAIN_LOG) 2>&1 &

.PHONY:			config
config:

			$(ENTRY) info -i config $(SID_ARGS) > config.txt

.PHONY:			confighead
confighead:

			$(ENTRY) info -i config $(HEADER_ARGS) > config.txt

.PHONY:			secprod
secprod:
			$(ENTRY) trainprod $(SID_ARGS) -p
			$(ENTRY) pack $(SID_ARGS)

.PHONY:			headertraintest
headertraintest:
			$(ENTRY) traintest $(HEADER_ARGS) -p

.PHONY:			headerprod
headerprod:
			$(ENTRY) trainprod $(HEADER_ARGS) -p
			$(ENTRY) pack $(HEADER_ARGS)

.PHONY:			trainfast
trainfast:
			$(ENTRY) traintest $(SID_ARGS) -p --override \
			  'model_settings.epochs=2,batch_stash.batch_limit=3'

.PHONY:			cleanbatch
cleanbatch:
			rm -rf target model data
			$(ENTRY) batch -c etc/batch.conf

.PHONY:			stop
stop:
			mkdir -p data/model/model
			touch data/model/model/update.json

.PHONY:			hardstop
hardstop:
			ps -eaf | grep python | grep $(ENTRY) | \
				grep -v grep | awk '{print $$2}' | xargs kill

.PHONY:			data-clean
data-clean:		clean
			rm -f *.log
			make -C docker/app cleanall
