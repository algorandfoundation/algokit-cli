#!/bin/bash

#script arguments
wheel_files=( $1 )
wheel_file=${wheel_files[0]}
homebrew_tap_repo=$2

#error codes
MISSING_WHEEL=1
RESOURCE_GENERATION_FAILED=2
FORMULA_GENERATION_FAILED=3
PR_CREATION_FAILED=4

if [[ ! -f $wheel_file ]]; then
  >&2 echo "$wheel_file not found. 🚫"
  exit $MISSING_WHEEL
else
  echo "Found $wheel_file 🎉"
fi

create_resources() {
  local wheel=`realpath $1`
  local package=$2
  local output=$3

  echo "Creating temp directory."
  local temp=`mktemp -d`
  pushd $temp >/dev/null

  echo "Creating python virtual environment."
  python3 -m venv venv
  source venv/bin/activate

  echo "Using poet to generate resources."
  pip install $wheel homebrew-pypi-poet
  #also strip out resource block for referenced package
  local resources=`poet $package | sed "/resource \"$package\" do/{N;N;N;N;d;}"`

  echo "Cleanup."
  deactivate
  popd >/dev/null
  rm -rf $temp
  
  echo "Saving resources to $output"
  echo "$resources" > $output
  lines=`wc -l < $output`
  
  expected_lines=4 #assumption that there is at least one dependency
  if [[ ! -f $output || "$lines" -lt "$expected_lines" ]]; then
    >&2 echo "Failed to generate $output 🚫"
    exit $RESOURCE_GENERATION_FAILED
  else
    echo "Created $output 🎉"
  fi
}

get_metadata() {
  local field=$1
  grep "^$field:" $metadata | cut -f 2 -d : | xargs
}

create_formula() {
  repo="https://github.com/${GITHUB_REPOSITORY}"
  homepage="$repo"
  
  wheel=`basename $wheel_file`
  echo "Creating brew formula from $wheel_file"

  #determine version and release tag from .whl
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

  url="$repo/archive/refs/tags/$release_tag.tar.gz"
  #get other metadata from wheel
  unzip -o $wheel_file -d . >/dev/null 2>&1
  metadata=`echo $wheel | cut -f 1,2 -d "-"`.dist-info/METADATA

  command=`get_metadata Name`
  desc=`get_metadata Summary`
  license=`get_metadata License`

  echo "Calculating sha256 of $url..."
  sha256=`curl -s -L $url | sha256sum | cut -f 1 -d ' '`

  echo "Determining resources for $command..."
  create_resources $wheel_file $command resources.txt
  resources=`cat resources.txt`

  formula=`echo ${command:0:1} | tr  '[a-z]' '[A-Z]'`${command:1}
  ruby=${command}.rb
  head="git+$repo.git"

  echo "Outputting $ruby..."

cat << EOF > $ruby
class $formula < Formula
  include Language::Python::Virtualenv

  desc "$desc"
  homepage "$homepage"
  url "$url"
  sha256 "$sha256"
  license "$license"
  head "$head", branch: "main"

  depends_on "pipx"
  depends_on "python@3.10"

$resources

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_equal "$command, version $version", shell_output(bin/"$command --version").strip
  end
end
EOF

  if [[ ! -f $ruby ]]; then
    >&2 echo "Failed to generate $ruby 🚫"
    exit $FORMULA_GENERATION_FAILED
  else
    echo "Created $ruby 🎉"
  fi
}

create_pr() {
  export GH_TOKEN=$TAP_GITHUB_TOKEN
  local full_ruby=`realpath $ruby`  
  echo "Cloning $homebrew_tap_repo..."
  clone_dir=`mktemp -d`
  git clone "https://${TAP_GITHUB_TOKEN}@github.com/${homebrew_tap_repo}.git" $clone_dir

  echo "Commiting Formula/$ruby..."
  pushd $clone_dir
  dest_branch="$command-update-$version"
  git checkout -b $dest_branch
  mkdir -p $clone_dir/Formula
  cp $full_ruby $clone_dir/Formula
  git add .
  git commit --message "Updating $command to $version"

  echo "Pushing $dest_branch..."
  git push -u origin HEAD:$dest_branch

  echo "Creating a pull request..."
  gh pr create --fill
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

create_formula
create_pr

echo Done.
echo
