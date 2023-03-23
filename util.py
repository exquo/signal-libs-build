#!/usr/bin/env python3

import os
import sys


def gha_set_output_param(name, value):
    gh_output_file = os.environ["GITHUB_OUTPUT"]
    with open(gh_output_file, 'a') as gh_out:
        gh_out.write(f"{name}={value}\n")


if __name__ == "__main__":
    fn = globals()[sys.argv[1]]
    fn(*sys.argv[2:])
