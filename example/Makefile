#
# Run install_packages as root. 
# Then run local_install from current directory (for local install + app build).
#

SHELL = bash

DJANGO_DIR = dj
VIRTUAL_ENV = var/ve
LOCALPATH = $(CURDIR)
PYTHONPATH = $(LOCALPATH)/$(DJANGO_DIR)
DJANGO_TEST_PORTS = 9000-10000
SETTINGS = settings
DJANGO_SETTINGS_MODULE = $(DJANGO_DIR).settings.$(SETTINGS)
DJANGO_POSTFIX = --settings=$(DJANGO_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
PYTHON_BIN = $(VIRTUAL_ENV)/bin
PYTHON = python3
TYPE = dev
OS = $(shell uname)

INIT_DATA_PATH = data
INIT_DATA_FILE = $(INIT_DATA_PATH)/init.json
INIT_DATA_MEDIA = $(INIT_DATA_PATH)/media

test_modules = issue_tracker.tests

clean:
	find . -name "*.pyc" -delete;
	find . -type d -empty -delete;
	
cleanvirtualenv:
	rm -rf $(VIRTUAL_ENV)

cleanvar: clean cleanjs cleanvirtualenv
	rm -rf $(LOCALPATH)/var

cleanjs:
	rm -rf $(LOCALPATH)/node_modules $(LOCALPATH)/bower_components $(LOCALPATH)/static/js

cleanall: cleanvar

pip:
	$(PYTHON_BIN)/pip install --process-dependency-links --allow-all-external -r requirements/base.txt

initvirtualenv:
	virtualenv -p $(PYTHON) --no-site-packages $(VIRTUAL_ENV)
	$(PYTHON_BIN)/pip install --upgrade pip==1.5
	$(PYTHON_BIN)/pip install setuptools --no-use-wheel --upgrade

installjs:
	npm install
	bower install
	mkdir -p $(LOCALPATH)/static/js
	# install packages required by front-end
	ln -sf $(LOCALPATH)/var/cs/deps.js $(LOCALPATH)/bower_components/closure-library/closure/goog\
	 $(LOCALPATH)/var/cs/start.js $(LOCALPATH)/bower_components $(LOCALPATH)/static/js
	ln -sf $(LOCALPATH)/bower_components/d3/d3.min.js $(LOCALPATH)/static/js/d3.js
	ln -sf $(LOCALPATH)/bower_components/c3/c3.min.js $(LOCALPATH)/static/js/c3.js

buildjs:
	# build front-end (compile javacripts, etc)
	grunt dist

bootstrap: initvirtualenv pip

reinstallvirtualenv: cleanvirtualenv bootstrap initvirtualenv initenv

test: clean
	$(PYTHON_BIN)/coverage run --omit */site-packages/*,*/migrations/*,*/lib/* $(LOCALPATH)/manage.py test\
	 $(test_modules)  --liveserver=localhost:$(DJANGO_TEST_PORTS) $(DJANGO_POSTFIX) -v 2

htmlcoverage: test
	$(PYTHON_BIN)/coverage html -d $(LOCALPATH)/var/reports/htmlcov --omit */site-packages/*,*/migrations/*,*/lib/*
	$(OPENHTML) $(LOCALPATH)/var/reports/htmlcov/index.html

initdb:
	mkdir -p $(LOCALPATH)/var/db

syncdb:
	$(PYTHON_BIN)/python manage.py syncdb --noinput $(DJANGO_POSTFIX)
	$(MAKE) migrate

initdata: syncmedia
	if [ -a $(LOCALPATH)/$(INIT_DATA_FILE) ]; then $(PYTHON_BIN)/python manage.py loaddata $(LOCALPATH)/$(INIT_DATA_FILE) $(DJANGO_POSTFIX); fi;

migrate:
	$(PYTHON_BIN)/python manage.py migrate $(DJANGO_POSTFIX)

resetdb:
	$(PYTHON_BIN)/python manage.py reset_db --noinput $(DJANGO_POSTFIX)
	$(MAKE) syncdb

syncmedia:
	if [ -d "$(LOCALPATH)/$(INIT_DATA_MEDIA)" ]; then\
		cp -R $(LOCALPATH)/$(INIT_DATA_MEDIA)/* $(LOCALPATH)/media/;\
	fi;

initlog:
	mkdir -p $(LOCALPATH)/var/log

initenv:
	echo -e '\nDJANGO_SETTINGS_MODULE="$(DJANGO_SETTINGS_MODULE)"' >> $(VIRTUAL_ENV)/bin/activate
	echo -e 'export DJANGO_SETTINGS_MODULE' >> $(VIRTUAL_ENV)/bin/activate


callcommand:
	@$(PYTHON_BIN)/python manage.py $(command) $(DJANGO_POSTFIX)

showurls:
	$(PYTHON_BIN)/python manage.py show_urls $(DJANGO_POSTFIX)

runserver:
	$(PYTHON_BIN)/python manage.py runserver --insecure $(DJANGO_POSTFIX)

schemamigration:
ifeq ($(force), 1)
	-rm -rf "dj/apps/$(app)/migrations"
	$(PYTHON_BIN)/python manage.py schemamigration $(app) --initial $(DJANGO_POSTFIX)	
else ifneq ($(wildcard dj/apps/$(app)/migrations/0001_*),)
	$(PYTHON_BIN)/python manage.py schemamigration $(app) --auto $(DJANGO_POSTFIX)
else
	$(PYTHON_BIN)/python manage.py schemamigration $(app) --initial $(DJANGO_POSTFIX)
endif

datamigration:
	$(PYTHON_BIN)/python manage.py datamigration $(app) $(name) $(DJANGO_POSTFIX)

install: cleanvar bootstrap installjs initlog initdb syncdb initdata buildjs initenv

update: clean cleanvirtualenv cleanjs bootstrap syncdb installjs buildjs initenv

include build/Makefile.$(OS)


