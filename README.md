Automatic compilation of native libraries for the Signal messenger.


### What it is

A CI/CD workflow to automatically compile [libsignal](https://github.com/signalapp/libsignal), which is used by [signal-cli](https://github.com/AsamK/signal-cli) and other projects. This rust library needs to be built for each operating system and processor architecture where it is used. This repo provides pre-compiled binaries for some of the [popular platforms](#available-platforms).


### How to use it

#### With signal-cli

The compiled library files (`.so` / `.dylib` / `.dll`) can be incorporated into signal-cli according to the [instructions on its wiki](https://github.com/AsamK/signal-cli/wiki/Provide-native-lib-for-libsignal). For Linux, this amounts to swapping the `.so` files inside the `.jar` archives.

For example, for signal-cli v0.11.6 on ARM64, download `signal-cli-0.11.6-Linux.tar.gz` from [signal-cli's releases](https://github.com/AsamK/signal-cli/releases) and `libsignal_jni.so-v0.21.1-aarch64-unknown-linux-gnu.tar.gz` from [this repo's releases](/../../releases). Unpack downloaded files with `tar -xzf ….tar.gz`. Then replace the bundled `.so` object:

	zip -uj signal-cli-0.11.6/lib/libsignal-client-0.21.1.jar libsignal_jni.so


### How it works

The [workflow](.github/workflows) automatically checks for new releases in <https://github.com/signalapp/libsignal> repo. If one is available, it downloads and builds the native library objects.


#### Security

The files published in this repo's [releases](/../../releases) are compiled and uploaded by GitHub's CI infrastructure, following the steps in the [workflow files](.github/workflows). The [github-actions](https://github.com/apps/github-actions) bot authors every release. Additionally, a SHA checksum of every compiled file is printed out to the logs during the workflow run.

This means that the resulting binaries can be used with confidence that they were built by GitHub Actions by executing instructions in the open-source workflow files.


### Available platforms

- `x86_64-linux-gnu`
	Most desktop linuxes.
	Supports `glibc` versions less recent than that required for the upstream releases, which are built on the latest Ubuntu (see [signal-cli#643](https://github.com/AsamK/signal-cli/issues/643)).
- `x86_64-pc-windows`
	Windows, 64 bit.
- `x86_64-apple-darwin`
   MacOS, Intel 64 bit.
- `aarch64-apple-darwin`
	MacOS, ARM64.
- `aarch64-linux-gnu`
	Raspberry Pi 3,4; Pine A64; many SoC.
- `armv7-linux-gnueabihf`
	Raspberry Pi 2; many SoC.
- `i686-linux-gnu`
	32 bit Linux.
- `x86_64-linux-musl`
	Alpine Linux, OpenWRT; see [note](https://github.com/exquo/signal-libs-build/issues/19#issuecomment-2067638410-permalink).

Tip: on \*nix, use `uname -m` to get your device's architecture.


### Historical notes

- As of signal-cli `v0.10.3`, the macOS and Windows builds are bundled into the [official releases](https://github.com/AsamK/signal-cli/releases).

- As of libsignal-client `v0.10.0`, builds for x86_64 macOS and Windows are available in the [upstream releases](https://github.com/signalapp/libsignal-client/releases/), along with the usual Linux builds.

- As of libsignal-client [`v0.10.0`](https://github.com/signalapp/libsignal-client/releases/tag/v0.10.0), the zkgroup library is now incorporated into the libsignal-client.


### Similar projects

- https://gitlab.com/packaging/libsignal-client
- https://gitlab.com/signald/libraries/libsignal-client
- https://media.projektzentrisch.de/temp/signal-cli

Manual builds for Raspberry Pi:

- https://github.com/DutchForeigner/signal-cli_rpi
- https://github.com/bublath/FHEM-Signalbot
