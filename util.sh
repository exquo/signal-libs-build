#!/usr/bin/bash

set -e -o pipefail

release_name() {
	REPO=$1
	VERSION=$2
	REPO=$(echo "$REPO" | sed 's|.*/||')
	echo "${REPO}_${VERSION}"
}

get_latest_release_name() {
	REPO=${1:-$GITHUB_REPOSITORY}
	#echo "GETting: ${GITHUB_API_URL}/repos/${REPO}/releases/latest"
	latest_release_json=$(curl -sL \
		-H "Authorization: Bearer $GITHUB_TOKEN" \
		"${GITHUB_API_URL}/repos/${REPO}/releases/latest")
	#echo "latest_release_json = $latest_release_json"
	echo "$latest_release_json" | jq -r '.name'
}

get_release_data() {
	RELEASE_NAME=$1
	REPO=${2:-$GITHUB_REPOSITORY}
	#GITHUB_TOKEN=$3
	releases_json=$(curl -s \
		-H "Authorization: Bearer $GITHUB_TOKEN" \
		"${GITHUB_API_URL}/repos/${REPO}/releases")
	echo "$releases_json" | jq -c ".[] | select (.tag_name == \"$RELEASE_NAME\")"
}

dl_release_asset() {
	REPO=$1
	RELEASE_NAME=$2
	FILE_NAME=$3
	#GITHUB_TOKEN=$4
	release_data=$(get_release_data "$RELEASE_NAME" "$REPO" "$GITHUB_TOKEN")
	echo "$release_data"
	asset_dl_url=$(echo "$release_data" | jq -r ".assets[] | select (.name == \"$FILE_NAME\") | .url")
	echo "$asset_dl_url"
	#[ -n "$asset_dl_url" ]  # quit if dl_url empty; actually, curl will fail
	curl -sLOJ \
		-H 'Accept: application/octet-stream' \
		-H "Authorization: Bearer $GITHUB_TOKEN" \
		"$asset_dl_url"
}

dl_libs_for_matrix() {
	MATRIX="$1"
	RUNNER="$2"
	REPO="${3:-$GITHUB_REPOSITORY}"
	#GITHUB_TOKEN=$4
	#IFS=$'\n'
	#for lib in $(echo $MATRIX | jq -c '.lib[]'); do
	#SCRIPT_DIR=$(dirname "$(readlink -f "$0")")  # `readlink -f` does not work on MacOS
	SCRIPT_DIR=$(dirname "$0")
	echo "$MATRIX" | jq -c '.lib[]' | while read lib; do
		echo "$lib" #| jq .
		lib_name=$(echo $lib | jq -r '.name')
		echo $lib_name
		filename=$(python3 "$SCRIPT_DIR"/filename_for_matrix_item.py "$MATRIX" "$lib_name" "$RUNNER" \
			| sed -n 's/.*archive_name:://p').tar.gz
		echo "$filename"
		release_name=$(release_name "$(echo "$lib" | jq -r '.repo')"  "$(echo "$lib" | jq -r '.ref')" )
		echo "$release_name"
		dl_release_asset "$REPO" "$release_name" "$filename"
	done
}

find_signal_cli_jars_vers() {
	MATRIX="$1"
	SIGNAL_CLI_LIB_DIR=./build/install/signal-cli/lib/
	echo "$MATRIX" | jq -c '.lib[]' | while read lib; do
		lib_name=$(echo "$lib" | jq -r '.name')
		jar_prefix=$(echo "$lib" | jq -r '.jar_name')-
		jar_version=$(find "$SIGNAL_CLI_LIB_DIR" -name "$jar_prefix*.jar" | xargs basename | sed "s/$jar_prefix//; s/.jar//")
		echo "$jar_version"
		echo "::set-output name=$lib_name::v$jar_version" # Note: added "v"
	done
}

swap_signal_cli_jar_libs() {
	MATRIX=$1
	LIB_DIR=$2
	echo "$MATRIX" | jq -c '.lib[]' | while read lib; do
		lib_name=$(echo "$lib" | jq -r '.name')
		## Find the jar file
		jar_prefix=$(echo "$lib" | jq -r '.jar_name')-
		jar_file=$(find "$LIB_DIR" -name "$jar_prefix*.jar")
		echo "$jar_file"
		## Remove the .so file inside the .jar's
		lib_filename_root=$(echo "$lib" | jq -r '.filename')
		lib_filename_linux="lib${lib_filename_root}.so"
		zip -d "$jar_file" "$lib_filename_linux"
		if [[ ! "$RUNNER_OS" == 'Windows' ]]; then
			## Add lib files to .jar's
			zip -j "$jar_file" "$GITHUB_WORKSPACE"/*"${lib_filename_root}"*
		fi
	done
	if [[ "$RUNNER_OS" == 'Windows' ]]; then
		# On windows, files can't be bundled inside .jar's
		cd "$LIB_DIR"
		mkdir dll
		cp "$GITHUB_WORKSPACE"/*.dll  ./dll
		ls -la ./dll
	fi
}

gradle_deps_vers () {
	# UPD: No longer works (last working libsignal-service-java..unofficial_27)
		# Now extracting info from `witness-verifications.gradle` file.
	# Extract libs verion numbers from build.gradle files.
		# This method is not very reliable, since that file format is not rigid and can change, breaking the existing parsing scheme.
		# Alternatively, can use gradle itself:
			# https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html
			# https://mkyong.com/gradle/gradle-display-project-dependency/
	grep -E 'api.*(zkgroup|signal-client)' service/build.gradle | \
		while read line; do
			# Replace ${VARIABLE} with its value from `build.gradle` file
			var_name=$(echo "$line" | sed -nE 's/.*[\$]\{(.*)\}.*/\1/p')
			if [[ -z "$var_name" ]]; then
				# The $line contains explicit ver (e.g. "1.2.3") rather than variable ref (e.g. "${SOME_VER}")
				echo "$line"
				continue
			fi
			ver=$(sed -nE "s/.*ext\.$var_name\s*=\s*\"(.*)\"/\1/p" build.gradle)
			echo "$line" | sed -nE "s/[\$]\{(.*)\}/$ver/p"
		done
}

add_deb_repos() {
	# Installing GitHub CLI `gh` on Debian container
	# From https://github.com/cli/cli/blob/trunk/docs/install_linux.md, sans `sudo` (for docker)
	type -p curl >/dev/null || apt install curl -y
	curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
	&& chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null

	# For installing newer protobuf-compiler than available on Debian 10 (buster)
	# Need protoc>v3.12.0, or get "protoc failed: Unknown flag: --experimental_allow_proto3_optional"
	#echo "deb http://deb.debian.org/debian buster-backports main" > /etc/apt/sources.list.d/buster-backports.list
		# buster-backports was moved to `archive`
		# https://lists.debian.org/debian-devel-announce/2024/03/msg00003.html
	#echo "deb http://archive.debian.org/debian buster-backports main" > /etc/apt/sources.list.d/buster-backports.list
}

install_protobuf() {
	VER=$PROTOBUF_VER
	FNAME=protoc-${VER}-linux-x86_64.zip
	curl -LO https://github.com/protocolbuffers/protobuf/releases/download/v${VER}/${FNAME}
	unzip "$FNAME" -d /usr/local
	protoc --version
}

install_rust () {
	# Ref: https://github.com/rust-lang/docker-rust/blob/master/Dockerfile-slim.template
	export RUSTUP_HOME=/usr/local/rustup
	export CARGO_HOME=/usr/local/cargo
	export PATH=/usr/local/cargo/bin:$PATH
	echo "RUSTUP_HOME=/usr/local/rustup" >> "$GITHUB_ENV"
	echo "CARGO_HOME=/usr/local/cargo" >> "$GITHUB_ENV"
	echo "/usr/local/cargo/bin" >> "$GITHUB_PATH"
	curl -LO https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init
	chmod +x rustup-init
	./rustup-init -y --no-modify-path --profile minimal --default-toolchain nightly
	rustc --version; cargo --version; rustup --version;
}

install_dependencies_deb () {
	install_protobuf
}

"$@"
