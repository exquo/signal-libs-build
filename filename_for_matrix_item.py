#!/usr/bin/env python3

import json
import os
import sys

matrix = json.loads(sys.argv[1])
lib_name = sys.argv[2]
host_runner = sys.argv[3]
try:
    cross_target = sys.argv[4]
except IndexError:
    cross_target = None

def get_matrix_item(matrix, matrix_key, list_key, list_key_val):
    matrix_key_list = matrix.get(matrix_key) or []
    for item in matrix_key_list:
        if item and item[list_key] == list_key_val:
            return item
    for item in matrix["include"]:
        include_item = item[matrix_key]
        if include_item[list_key] == list_key_val:
            return include_item
    raise ValueError

lib_dict = get_matrix_item(matrix, "lib", "name", lib_name)
host_dict = get_matrix_item(matrix, "host", "runner", host_runner)
cross_dict = get_matrix_item(matrix, "cross", "target", cross_target) if cross_target else None

lib_filename = "".join([
    host_dict.get("lib-prefix") or "",
    lib_dict["filename"],
    host_dict["lib-suffix"]
    ])
print(lib_filename)

archive_name = "".join([
    lib_filename,
    "-",
    lib_dict["ref"],
    "-",
    cross_dict["target"] if cross_dict else host_dict["triple"]
    ])
print(archive_name)

gh_output_file = os.environ["GITHUB_OUTPUT"]
with open(gh_output_file, 'a') as gh_out:
    gh_out.write('\n'.join((
        f"lib_filename={lib_filename}",
        f"archive_name={archive_name}",
        ''
        )))
