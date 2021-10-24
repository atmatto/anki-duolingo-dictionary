#!/bin/bash

rm -r ~/.local/share/Anki2/addons21/DuolingoDictionary/
mkdir ~/.local/share/Anki2/addons21/DuolingoDictionary/
cp -r __init__.py icon config.md manifest.json ~/.local/share/Anki2/addons21/DuolingoDictionary/
# config-test.json will be used instead of config.json if it exists
[ -f config-test.json ] && cp config-test.json ~/.local/share/Anki2/addons21/DuolingoDictionary/config.json || cp config.json ~/.local/share/Anki2/addons21/DuolingoDictionary/config.json
anki