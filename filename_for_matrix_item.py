#!/usr/bin/env python3

import json
import sys

import util


matrix_run = json.loads(sys.argv[1])

lib = matrix_run["lib"]
build_env = matrix_run["build-env"]

lib_filename = "".join((
    build_env.get("lib-prefix") or "",
    lib["filename"],
    build_env["lib-suffix"]
    ))
print(lib_filename)

archive_name = "".join((
    lib_filename,
    "-",
    lib["ref"],
    "-",
    build_env.get("target") or build_env["triple"]
    ))
print(archive_name)

util.gha_set_output_param("lib_filename", lib_filename)
util.gha_set_output_param("archive_name", archive_name)
