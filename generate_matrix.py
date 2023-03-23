#!/usr/bin/env python3

import json
import pprint
import sys

import util


print(sys.argv)
libs_ver= {"libsignal": sys.argv[1]}

libs = {
        "libsignal": {
            "repo": "signalapp/libsignal",
            "filename": "signal_jni",
            "cargo-flags": "-p libsignal-jni",
            },
        #"zkgroup": {
            ### UPD: zkgroup is included in libsignal-client v0.10.0, and is no longer a dependency in libsignal-service-java
            #"repo": "signalapp/zkgroup",
            #"jar_name": "zkgroup-java",
            #"filename": "zkgroup",
            #},
        }

hosts = {
        "linux": {
                "runner": "ubuntu-20.04",
                "lib-prefix": "lib",
                "lib-suffix": ".so",
                "triple": "x86_64-unknown-linux-gnu",
                "install-cmd": "sudo apt-get update && sudo apt-get install",
                },
        "macos": {
                "runner": "macos-latest",
                "lib-prefix": "lib",
                "lib-suffix": ".dylib",
                "triple": "x86_64-apple-darwin",
            },
        "windows": {
                "runner": "windows-latest",
                "lib-suffix": ".dll",
                "triple": "x86_64-pc-windows",
                "install-cmd": "choco install",
                "req-pkg": "nasm",  # for boringssl
                "rust-flags": "-C target-feature=+crt-static",
                    # Static linking to remove MSVC dependendency. See:
                    # zkgroup/ffi/node/Makefile
                    # libsignal-client/node/build_node_bridge.py
                },
        }

def cross_template(arch, subarch="", env="gnu", vendor="unknown", sys_os="linux", compilers=None):
    compilers = compilers or {"C": "gcc", "C++": "g++"}
    host_dict = hosts.get(sys_os, {})
    cross_dict = {
            "target": f"{arch}{subarch}-{vendor}-{sys_os}-{env}",
            "req-pkg": " ".join((
                f"{compiler}-{arch}-{sys_os}-{env}" for compiler in compilers.values()
                )),
            "linker": f"{arch}-{sys_os}-{env}-{compilers['C']}",
            "build-env-vars": " ".join((
                f"CC={arch}-{sys_os}-{env}-{compilers['C']}",
                f"CXX={arch}-{sys_os}-{env}-{compilers['C++']}",
                f"CPATH=/usr/{arch}-{sys_os}-{env}/include",
                )),
            }
    return host_dict | cross_dict

build_envs = [
        hosts["linux"] | {
            ### Rust container on Debian 10
            "container": "rust:buster",
            "install-cmd": "bash ./util.sh add_gh_ppa && apt-get update && apt-get install -y",
            "req-pkg": "python3 clang libclang-dev cmake make gh",
            },
        hosts["macos"],
        hosts["windows"],
        ### Cross-compiling ###
        cross_template("aarch64"),
        cross_template("arm", "v7", "gnueabihf"),
        cross_template("i686"),
        hosts["macos"] | {"target": "aarch64-apple-darwin"},
        ]


for lib_name, lib_ver in libs_ver.items():
    libs[lib_name]["ref"] = lib_ver

matrix = {
        "lib": list(libs.values()),
        "build-env": build_envs,
        "include": [],
        }

jobs_total = len(libs) * len(build_envs) + len(matrix.get("include", []))
print("Total num of jobs:", jobs_total)

pprint.pprint(matrix)
util.gha_set_output_param("matrix", json.dumps(matrix))
