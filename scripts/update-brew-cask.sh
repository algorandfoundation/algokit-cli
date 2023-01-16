#!/bin/bash

#script arguments
wheel_files=( $1 )
wheel_file=${wheel_files[0]}
homebrew_tap_repo=$2

#globals
command=algokit

#error codes
MISSING_WHEEL=1
CASK_GENERATION_FAILED=2
PR_CREATION_FAILED=3

if [[ ! -f $wheel_file ]]; then
  >&2 echo "$wheel_file not found. 🚫"
  exit $MISSING_WHEEL
else
  echo "Found $wheel_file 🎉"
fi

get_metadata() {
  local field=$1
  grep "^$field:" $metadata | cut -f 2 -d : | xargs
}

create_cask() {
  repo="https://github.com/${GITHUB_REPOSITORY}"
  homepage="$repo"
  
  wheel=`basename $wheel_file`
  echo "Creating brew cask from $wheel_file"

  #determine package_name, version and release tag from .whl
  package_name=`echo $wheel | cut -d- -f1`

  version=None
  version_regex="-([0-9]+\.[0-9]+\.[0-9]+)b?([0-9]*)-"
  if [[ $wheel_file =~ $version_regex ]]; then
    version=${BASH_REMATCH[1]}
    version_beta=${BASH_REMATCH[2]}
  fi

  release_tag="v${version}"
  if [[ -n $version_beta ]]; then
    release_tag=${release_tag}-beta.${version_beta}
  fi

  echo Version: $version
  echo Release Tag: $release_tag

  url="$repo/releases/download/$release_tag/$wheel"
  #get other metadata from wheel
  unzip -o $wheel_file -d . >/dev/null 2>&1
  metadata=`echo $wheel | cut -f 1,2 -d "-"`.dist-info/METADATA

  desc=`get_metadata Summary`
  license=`get_metadata License`

  echo "Calculating sha256 of $url..."
  sha256=`curl -s -L $url | sha256sum | cut -f 1 -d ' '`

  ruby=${command}.rb
  
  echo "Outputting $ruby..."

cat << EOF > $ruby
# typed: false
# frozen_string_literal: true

cask "$command" do
  version "$version"
  sha256 "$sha256"

  url "$repo/releases/download/v#{version}/algokit-#{version}-py3-none-any.whl"
  name "$command"
  desc "$desc"
  homepage "$homepage"

  depends_on formula: "pipx"
  container type: :naked

  installer script: {
    executable:   "pipx",
    args:         ["install", "--force", "#{staged_path}/$wheel"],
    print_stderr: false,
  }
  installer script: {
    executable: "bash",
    args:       ["-c", "echo \$(which pipx) uninstall $package_name >#{staged_path}/uninstall.sh"],
  }

  uninstall script: {
    executable: "bash",
    args:       ["#{staged_path}/uninstall.sh"],
  }
end
EOF

  if [[ ! -f $ruby ]]; then
    >&2 echo "Failed to generate $ruby 🚫"
    exit $CASK_GENERATION_FAILED
  else
    echo "Created $ruby 🎉"
  fi
}

create_pr() {
  local full_ruby=`realpath $ruby`  
  echo "Cloning $homebrew_tap_repo..."
  clone_dir=`mktemp -d`
  git clone "https://oauth2:${TAP_GITHUB_TOKEN}@github.com/${homebrew_tap_repo}.git" $clone_dir

  echo "Commiting Casks/$ruby..."
  pushd $clone_dir
  dest_branch="$command-update-$version"
  git checkout -b $dest_branch
  mkdir -p $clone_dir/Casks
  cp $full_ruby $clone_dir/Casks
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
