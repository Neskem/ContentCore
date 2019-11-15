#!/bin/bash

# rename files which extension is so
find ./breakcontent -name '*.so' | awk -F '.cpython-36m-x86_64-linux-gnu' '{print "mv "$0" "$1$2}' | sh

# delete py files after rename so files
# shellcheck disable=SC2038
find ./breakcontent  -name '*.py' | xargs rm -f
rm -rf build
