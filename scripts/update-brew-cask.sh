#!/bin/bash

#script arguments
wheel_files=( $1 )
wheel_file=${wheel_files[0]}
arm_artifacts=( $2 )
arm_artifact=${arm_artifacts[0]}
intel_artifacts=( $3 )
intel_artifact=${intel_artifacts[0]}
homebrew_tap_repo=$4

#globals
command=algokit

#error codes
MISSING_WHEEL=1
MISSING_EXECUTABLE=2
CASK_GENERATION_FAILED=3
PR_CREATION_FAILED=4

if [[ ! -f $wheel_file ]]; then
  >&2 echo "$wheel_file not found. 🚫"
  exit $MISSING_WHEEL
else
  echo "Found $wheel_file 🎉"
fi

if [[ ! -f $arm_artifact ]]; then
  >&2 echo "$arm_artifact not found. 🚫"
  exit $MISSING_EXECUTABLE
else
  echo "Found $arm_artifact 🎉"
fi

if [[ ! -f $intel_artifact ]]; then
  >&2 echo "$intel_artifact not found. 🚫"
  exit $MISSING_EXECUTABLE
else
  echo "Found $intel_artifact 🎉"
fi


get_metadata() {
  local field=$1
  grep "^$field:" $metadata | cut -f 2 -d : | xargs
}

create_cask() {
  repo="https://github.com/${GITHUB_REPOSITORY}"
  homepage="$repo"
  
  echo "Creating brew cask"

  # determine package_name, version and release tag from .whl
  wheel=`basename $wheel_file`
  package_name=`echo $wheel | cut -d- -f1`

  version=None
  version_regex="-([0-9]+\.[0-9]+\.[0-9]+)b?([0-9]*)-"
  if [[ $wheel_file =~ $version_regex ]]; then
    version=${BASH_REMATCH[1]}
    version_beta=${BASH_REMATCH[2]}
  fi

  release_tag="${version}"
  if [[ -n $version_beta ]]; then
    release_tag=${release_tag}-beta.${version_beta}
  fi

  echo Version: $version
  echo Release Tag: $release_tag

  # get other metadata from wheel
  unzip -o $wheel_file -d . >/dev/null 2>&1
  metadata=`echo $wheel | cut -f 1,2 -d "-"`.dist-info/METADATA

  desc=`get_metadata Summary`
  license=`get_metadata License`

  arm_binary_url="$repo/releases/download/$release_tag/$(basename $arm_artifact)"
  echo "Calculating sha256 of $arm_binary_url..."
  arm_sha256=`curl -s -L $arm_binary_url | sha256sum | cut -f 1 -d ' '`

  intel_binary_url="$repo/releases/download/$release_tag/$(basename $intel_artifact)"
  echo "Calculating sha256 of $intel_binary_url..."
  intel_sha256=`curl -s -L $intel_binary_url | sha256sum | cut -f 1 -d ' '`

  cask_file=${command}.rb
  
  echo "Outputting $cask_file..."

cat << EOF > $cask_file
cask "$package_name" do
  arch arm: "arm64", intel: "x64"
  version "$version"
  sha256 arm: "$arm_sha256", intel: "$intel_sha256"

  url "$repo/releases/download/v#{version}/algokit-v#{version}-macos_#{arch}.tar.gz"
  name "$package_name"
  desc "$desc"
  homepage "$homepage"

  binary "#{staged_path}/#{token}"

  postflight do
    set_permissions "#{staged_path}/#{token}", "0755"
  end

  uninstall delete: "/usr/local/bin/#{token}"
end
EOF

  if [[ ! -f $cask_file ]]; then
    >&2 echo "Failed to generate $cask_file 🚫"
    exit $CASK_GENERATION_FAILED
  else
    echo "Created $cask_file 🎉"
  fi
}

create_pr() {
  local full_cask_filepath=`realpath $cask_file`  
  echo "Cloning $homebrew_tap_repo..."
  clone_dir=`mktemp -d`
  git clone "https://oauth2:${TAP_GITHUB_TOKEN}@github.com/${homebrew_tap_repo}.git" $clone_dir

  echo "Commiting Casks/$cask_file..."
  pushd $clone_dir
  dest_branch="$command-update-$version"
  git checkout -b $dest_branch
  mkdir -p $clone_dir/Casks
  cp $full_cask_filepath $clone_dir/Casks
  message="Updating $command to $version"
  git add .
  git commit --message "$message"

  echo "Pushing $dest_branch..."
  git push -u origin HEAD:$dest_branch

  echo "Creating a pull request..."
  # can't use gh because it doesn't support fine grained access tokens yet https://github.com/github/roadmap/issues/622
cat << EOF > pr_body.json
{
  "title": "${message}",
  "head": "${dest_branch}",
  "base": "main"
}
EOF

  curl \
    --fail \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $TAP_GITHUB_TOKEN"\
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/${homebrew_tap_repo}/pulls \
    -d @pr_body.json
  pr_exit_code=$?

  popd

  echo "Cleanup."
  rm -rf $clone_dir

  if [[ $pr_exit_code != 0 ]]; then
    >&2 echo "PR creation failed 🚫"
    exit $PR_CREATION_FAILED
  else
    echo "PR creation successful 🎉"
  fi
}

create_cask
create_pr

echo Done.
echo
