#!/bin/zsh
source ~/.zshrc
sindarin
pypush ../../ext
pypush ../
python ../../ext/proxpy/proxpy.py -x proxypy_plugin.py
