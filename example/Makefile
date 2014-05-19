#
# Run install_packages as root. 
# Then run local_install from current directory (for local install + app build).
#

SHELL = bash

VIRTUAL_ENV = var/ve
LOCALPATH = $(CURDIR)
PYTHONPATH = $(LOCALPATH)/$(DJANGO_DIR)
DJANGO_SETTINGS_MODULE = settings
DJANGO_POSTFIX = --settings=$(DJANGO_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
PYTHON_BIN = $(VIRTUAL_ENV)/bin


clean:
	find . -name "*.pyc" -delete;
	find . -type d -empty -delete;


cleanvirtualenv:
	rm -rf $(VIRTUAL_ENV)


cleanvar: clean cleanvirtualenv
	rm -rf $(LOCALPATH)/var


cleanall: cleanvar cleandb


pip:
	$(PYTHON_BIN)/pip install --process-dependency-links --allow-all-external -r requirements/base.txt


initvirtualenv:
	virtualenv --no-site-packages $(VIRTUAL_ENV)
	$(PYTHON_BIN)/pip install --upgrade pip==1.5
	$(PYTHON_BIN)/pip install setuptools --no-use-wheel --upgrade


bootstrap: initvirtualenv pip


reinstallvirtualenv: cleanvirtualenv bootstrap initvirtualenv initenv


initdb:
	mkdir -p $(LOCALPATH)/var/db


syncdb:
	$(PYTHON_BIN)/python manage.py syncdb --noinput $(DJANGO_POSTFIX)


migrate:
	$(PYTHON_BIN)/python manage.py migrate $(DJANGO_POSTFIX)


initlog:
	mkdir -p $(LOCALPATH)/var/log


initenv:
	echo -e '\nDJANGO_SETTINGS_MODULE="$(DJANGO_SETTINGS_MODULE)"' >> $(VIRTUAL_ENV)/bin/activate
	echo -e 'export DJANGO_SETTINGS_MODULE' >> $(VIRTUAL_ENV)/bin/activate


generatesettings: cleansettings
	@python build/hooks/generate_file_from_template.py \
		$(LOCALPATH)/$(DJANGO_DIR)/settings/$(SETTINGS).py \
		$(LOCALPATH)/$(DJANGO_DIR)/settings/$(SETTINGS).pytmp \
		CONFIG_FILE=$(LOCALPATH)/build/$(SETTINGS_CONFIG) \


installjs:
	npm install
	bower install
	mkdir -p $(LOCALPATH)/static/js
	# install packages required by front-end
	ln -sf $(LOCALPATH)/var/cs/deps.js $(LOCALPATH)/bower_components/closure-library/closure/goog\
	 $(LOCALPATH)/var/cs/start.js $(LOCALPATH)/var $(LOCALPATH)/bower_components $(LOCALPATH)/static/js
	ln -sf $(LOCALPATH)/bower_components/d3/d3.min.js $(LOCALPATH)/static/js/d3.js
	ln -sf $(LOCALPATH)/bower_components/d3-tip/index.js $(LOCALPATH)/static/js/d3-tip.js


buildjs:
	# build front-end (compile javacripts, etc)
	grunt dist


runserver:
	$(PYTHON_BIN)/python manage.py runserver --insecure $(DJANGO_POSTFIX)


callcommand:
	@$(PYTHON_BIN)/python manage.py $(command) $(DJANGO_POSTFIX)


install: cleanvar bootstrap initlog initdb syncdb initenv

update: clean cleanvirtualenv bootstrap syncdb initenv
