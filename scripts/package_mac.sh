#!/bin/bash

CMD="pyinstaller --clean --onedir --hidden-import jinja2_ansible_filters --hidden-import multiformats_config --copy-metadata algokit --name algokit --noconfirm src/algokit/__main__.py --add-data './misc/multiformats_config/multibase-table.json:multiformats_config/' --add-data './misc/multiformats_config/multicodec-table.json:multiformats_config/' --add-data './src/algokit/resources:algokit/resources/'"

if [ ! -z "$APPLE_BUNDLE_ID" ]; then
    CMD="$CMD --osx-bundle-identifier \"$APPLE_BUNDLE_ID\""
fi

if [ ! -z "$APPLE_CERT_ID" ]; then
    CMD="$CMD --codesign-identity \"$APPLE_CERT_ID\""
fi

if [ -f "./entitlements.xml" ]; then
    CMD="$CMD --osx-entitlements-file './entitlements.xml'"
fi

eval $CMD 
