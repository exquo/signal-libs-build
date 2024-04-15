#!/usr/bin/env python3

import json
import pprint
import sys

import util


print(sys.argv)
libs_ver = {"libsignal": sys.argv[1]}

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
        "linux-gnu": {
                "runner": "ubuntu-20.04",
                "lib-prefix": "lib",
                "lib-suffix": ".so",
                "triple": "x86_64-unknown-linux-gnu",
                "install-cmd": "sudo apt-get update && sudo apt-get install",
                "req-pkg": "protobuf-compiler"
                } | {
                ### Rust container on Debian 10
                ### (libc: Deb-10's v2.28 vs Ubuntu-20.04 v2.31)
                "container": "rust:buster",
                "install-cmd": "bash ./util.sh add_deb_repos && apt-get update && apt-get install -y",
                "req-pkg": "python3 clang libclang-dev cmake make gh protobuf-compiler/buster-backports",
                },
        "macos": {
                "runner": "macos-latest",
                "lib-prefix": "lib",
                "lib-suffix": ".dylib",
                "triple": "x86_64-apple-darwin",
                "install-cmd": "brew install",
                "req-pkg": "protobuf",
            },
        "windows": {
                "runner": "windows-latest",
                "lib-suffix": ".dll",
                "triple": "x86_64-pc-windows",
                "install-cmd": "choco install",
                "req-pkg": "nasm protoc",  # nasm: for boringssl
                "rust-flags": "-C target-feature=+crt-static",
                    # Static linking to remove MSVC dependendency. See:
                    # zkgroup/ffi/node/Makefile
                    # libsignal-client/node/build_node_bridge.py
                },
        "linux-musl": {
                "runner": "ubuntu-latest",
                "container": "rust:alpine",
                "lib-prefix": "lib",
                "lib-suffix": ".so",
                "triple": "x86_64-unknown-linux-musl",
                "install-cmd": "apk update && apk add",
                "req-pkg": "git bash python3 tar github-cli build-base gcc g++ clang clang-dev cmake make protobuf file openssl",
                "rust-flags": "-C target-feature=-crt-static",
                    # …-musl target linked statically by default
                    ## alt: use CARGO_CFG_TARGET_FEATURE env var
                #"cargo-flags": "--target=x86_64-unknown-linux-musl",
                },
        }

def cross_template(arch, subarch="", env="gnu", vendor="unknown", sys_os="linux", compilers=None, host_dict=None):
    compilers = compilers or {"C": "gcc", "C++": "g++"}
    host_dict = host_dict or hosts.get(f"{sys_os}-{'gnu' if env.startswith('gnu') else env}", {})
    cc =  f"{arch}-{sys_os}-{env}-{compilers['C']}"
    cxx = f"{arch}-{sys_os}-{env}-{compilers['C++']}"
    pkgs = " ".join((
        f"{compiler}-{arch}-{sys_os}-{env}" for compiler in compilers.values()
        )) if "apt-get" in host_dict["install-cmd"] else " ".join((
            cc, cxx
            ))
    cross_dict = {
            "target": f"{arch}{subarch}-{vendor}-{sys_os}-{env}",
            "req-pkg": " ".join((
                host_dict["req-pkg"],
                pkgs,
                )),
            "linker": cc,
            "build-env-vars": " ".join((
                f"CC={cc}",
                f"CXX={cxx}",
                f"CPATH=/usr/{arch}-{sys_os}-{env}/include",
                )),
            }
    return host_dict | cross_dict

build_envs = [
        hosts["linux"],
        hosts["macos"],
        hosts["windows"],
        ### Cross-compiling ###
        cross_template("aarch64"),
        cross_template("arm", "v7", "gnueabihf"),
        cross_template("i686"),
        hosts["macos"] | {"target": "aarch64-apple-darwin"},
        ### musl ###
        hosts["linux-musl"],
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
