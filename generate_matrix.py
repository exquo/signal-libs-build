#!/usr/bin/env python3

import json
import pprint
import sys

import util


print(sys.argv, file=sys.stderr)

libs = {
        "libsignal": {
                "repo": "signalapp/libsignal",
                "ref": sys.argv[1],
                "filename": "signal_jni",
                "cargo-flags": "-p libsignal-jni",
                },
        }

hosts = {
        "linux": {
                "runner": "ubuntu-latest",
                "triple": "x86_64-unknown-linux-gnu",
                "lib-prefix": "lib",
                "lib-suffix": ".so",
                }
        }
hosts = hosts | {
        "linux-gnu": hosts["linux"] | {
                "container": "rust:bullseye",
                "install-cmd": "apt-get update && apt-get install -y",
                "req-pkg": "python3 unzip gcc g++ git clang libclang-dev cmake make",
                    # "clang and libclang are used by boring-sys's bindgen; otherwise we could use plain old gcc and g++"
                    # (libsignal-client/java/Dockerfile)
                "setup-cmds": "bash ./util.sh install_dependencies_deb",
                "setup-env": " ".join((
                    "PROTOBUF_VER=25.4",
                    )),
                },
        "linux-gnu-rhel": hosts["linux"] | {
                "container": "rockylinux:8",
                "install-cmd": "dnf -y upgrade && dnf -y install",
                "req-pkg": "file git python3 unzip xz gcc gcc-c++ make cmake clang clang-libs",
                "setup-cmds": "bash ./util.sh install_dependencies_rhel",
                "setup-env": " ".join((
                    "PROTOBUF_VER=25.4",
                    )),
                },
        "linux-musl": hosts["linux"] | {
                "triple": "x86_64-unknown-linux-musl",
                "container": "rust:alpine",
                "install-cmd": "apk update && apk add",
                "req-pkg": "git bash python3 tar github-cli build-base gcc g++ clang clang-dev cmake make protobuf file openssl coreutils-env",
                "rust-flags": "-C target-feature=-crt-static",
                    # …-musl target linked statically by default
                    ## alt: use CARGO_CFG_TARGET_FEATURE env var
                #"cargo-flags": "--target=x86_64-unknown-linux-musl",
                },
        "macos": {
                "runner": "macos-latest",
                "triple": "aarch64-apple-darwin",
                    # macos-latest is arm64: https://github.com/actions/runner-images
                "lib-prefix": "lib",
                "lib-suffix": ".dylib",
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
        }

def cross_template(arch, subarch="", env="gnu", vendor="unknown", sys_os="linux", compilers=None, host_dict=None):
    compilers = compilers or {"C": "gcc", "C++": "g++"}
    host_dict = host_dict or hosts.get(f"{sys_os}-{'gnu' if env.startswith('gnu') else env}", {})
    cc =  f"{arch}-{sys_os}-{env}-{compilers['C']}"
    cxx = f"{arch}-{sys_os}-{env}-{compilers['C++']}"
    pkgs = " ".join((
        f"{compiler}-{arch}-{sys_os}-{env}" for compiler in compilers.values()
        ))
    return host_dict | {
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

build_envs = [
        hosts["linux-gnu-rhel"],
        hosts["linux-musl"],
        cross_template("aarch64"),
        cross_template("arm", "v7", "gnueabihf"),
        cross_template("i686"),
        hosts["macos"],
        hosts["macos"] | {"target": "x86_64-apple-darwin"},
        hosts["windows"],
        ]


matrix = {
        "lib": list(libs.values()),
        "build-env": build_envs,
        "include": [],
        }

jobs_total = len(libs) * len(build_envs) + len(matrix.get("include", []))
print("Total num of jobs:", jobs_total, file=sys.stderr)

pprint.pprint(matrix, stream=sys.stderr)
util.gha_set_output_param("matrix", json.dumps(matrix))
