## makefile automates the build and deployment for lein projects


## Build setup
#
# type of project, currently one of: clojure, python
PROJ_TYPE=		docker
PROJ_MODULES =		git
ADD_CLEAN_ALL +=	$(APP_MOUNT_DIR) $(APP_DATA_DIR)

# docker
DOCKER_IMG_NAME=	mimicsid
DOCKER_USER=		plandes
DOCKER_BUILD_OBJS=	$(MTARG)
DOCKER_CMP_CMD=		docker-compose --ansi never
DOCKER_CONTAINER=	$(DOCKER_IMG_NAME)
DOCKER_UP_DEPS +=	initsrc

# local user
DEV_USER =		devusr
DEV_CMD =		$(DOCKER_CMD) exec -u $(DEV_USER) -it $(DOCKER_CONTAINER)

# container paths
APP_MOUNT_DIR =		$(abspath src/mnt)
APP_DATA_DIR =		src/data


## Includes
#
include ../mimicdb/src/mk/client.mk
include ../../zenbuild/main.mk


## Targets
#
$(MTARG):
		mkdir -p $(MTARG)
		cp -r src/image $(MTARG)/inst

.PHONY:		initsrc
initsrc:
		mkdir -p $(MTARG)
		mkdir -p $(APP_MOUNT_DIR)
		mkdir -p $(APP_DATA_DIR)

.PHONY: 	devlogin
devlogin:
		$(DOCKER_CMD) exec -u $(DEV_USER) -i -t -w /home/$(DEV_USER) \
			$(DOCKER_CONTAINER) bash --login

# invoke a command (all paths/config files specified since not a login shell)
.PHONY:		invokecmd
invokecmd:
		$(DOCKER_CMD) exec -u $(DEV_USER) -t -w /home/$(DEV_USER) \
			$(DOCKER_CONTAINER) ./opt/lib/python/bin/$(CMD)

.PHONY:		testparse
testparse:
		make CMD="mednlp show 'John died of lung cancer.'" invokecmd


.PHONY:		testdumpadm
testdumpadm:
		make CMD="mimic -c /mnt/db.conf adm 193686" invokecmd

.PHONY:		testdumpnote
testdumpnote:
		make CMD="mimic -c /mnt/db.conf note 43290" invokecmd

.PHONY:		testdumpsec
testdumpsec:
		make CMD="mimicsid -c /mnt/db.conf note 43290" invokecmd
