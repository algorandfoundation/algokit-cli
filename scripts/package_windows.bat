@echo off
pyinstaller --clean --onedir --hidden-import jinja2_ansible_filters --hidden-import multiformats_config --copy-metadata algokit --name algokit --noconfirm src/algokit/__main__.py --add-data ./misc/multiformats_config;multiformats_config/ --add-data ./src/algokit/resources;algokit/resources/
