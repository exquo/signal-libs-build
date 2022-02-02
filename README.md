Automatic compilation of native libraries for the Signal messenger.

### What it is

This repo is a CI/CD workflow that uses GitHub Actions to automatically compile Signal's rust libraries [zkgroup](https://github.com/signalapp/zkgroup/) and [libsignal-client](https://github.com/signalapp/libsignal-client/). These libraries are required by the [libsignal-service-java (fork)](https://github.com/Turasa/libsignal-service-java/), which is in turn a dependency of [signal-cli](https://github.com/AsamK/signal-cli/). 

Using signal-cli currently requires compiling them individually for a specific operating system and a processor architecture. This repo aims to simplify the installation by providing the pre-compiled binaries for most of the popular platforms (see [available platforms](#available-platforms) below).

**Update**: As of libsignal-client [`v0.10.0`](https://github.com/signalapp/libsignal-client/releases/tag/v0.10.0), the zkgroup library is now incorporated into the libsignal-client.
**Update 2**: As of libsignal-client `v0.10.0`, builds for x86_64 macOS and Windows are available in the [upstream releases](https://github.com/signalapp/libsignal-client/releases/), along with the usual Linux builds.
**Update 3**: As of signal-cli `v0.10.3`, the macOS and Windows builds are bundled into the [official releases](https://github.com/AsamK/signal-cli/releases).



### How to use it

The compiled library files (`.so` / `.dylib` / `.dll`) can be incorporated into signal-cli according to the [instructions on its wiki](https://github.com/AsamK/signal-cli/wiki/Provide-native-lib-for-libsignal). For Linux, this amounts to swapping the `.so` files inside the `.jar` archives.
For example, for an ARM64 version of signal-cli v0.8.4.1, download the following files: `signal-cli-v0.8.4.1-x86_64-Linux.tar.gz`, `libsignal_jni.so-v0.8.1-aarch64-unknown-linux-gnu.tar.gz`, `libzkgroup.so-v0.7.0-aarch64-unknown-linux-gnu.tar.gz` and unpack them with `tar -xzf ….tar.gz`. Then execute the following commands:

	zip -uj signal-cli-<SIGNAL_CLI_VER>/lib/signal-client-java-<LIBCLIENT_VER>.jar  libsignal_jni.so
	zip -uj signal-cli-<SIGNAL_CLI_VER>/lib/zkgroup-java-<ZKGROUP_VER>.jar  libzkgroup.so

where substitute `<SIGNAL_CLI_VER>` with `v0.8.4.1`, `<LIBCLIENT_VER>` with `v0.7.0`, and `<ZKGROUP_VER>` with `v0.8.1`.


### How it works

The workflow automatically checks for new releases in https://github.com/Turasa/libsignal-service-java. If one is available, it downloads and builds the required versions of the native library dependencies.

#### Security

All the published files are compiled automatically by GitHub's CI infrastructure, following the steps in the [workflow files](.github/workflows). This can be verified by the "github-actions released this" line on the release's page (also visible with [GitHub API calls](https://docs.github.com/en/rest/reference/repos#get-the-latest-release)). Additionally, a SHA checksum is printed out during the workflow run for every compiled file.

All this means that you can download and run the published binaries with a confidence that they are exactly what has been produced by GitHub Actions by executing the instructions in the (open source) workflow files.


### Available platforms


- `x86_64-linux-gnu`
	Most desktop linuxes.
	Works with `glibc` v2.18 and newer, so that Ubuntu 18.04, Debain 10 and CentOS 7 are supported. (Upstream releases are built with a more recent `glibc` version. See [signal-cli#643](https://github.com/AsamK/signal-cli/issues/643))
- `x86_64-apple-darwin`
	MacOS, Intel 64 bit.
- `x86_64-pc-windows`
	Windows, 64 bit, statically linked (does not rely on the Microsoft Visual Code libraries).
- `aarch64-apple-darwin`
	MacOS, ARM64.
- `aarch64-linux-gnu`
	Raspberry Pi 3,4; Pine A64; many SoC.
- `armv7-linux-gnueabihf`
	Raspberry Pi 2; many SoC.
- `i686-linux-gnu`
	32 bit Linux.

Tip: on \*nix, use `uname -m` to get your device's architecture.

Suggestions for additional platforms are welcome - feel free to open an issue!


### Similar projects

- https://gitlab.com/signald/libraries/zkgroup 

Manual builds for Raspberry Pi:

- https://github.com/DutchForeigner/signal-cli_rpi
- https://github.com/bublath/FHEM-Signalbot/tree/main/armv7l
