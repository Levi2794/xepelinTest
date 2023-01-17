source scripts/common.sh

execute_release() {
  RELEASE_BRANCH=$1
  CURRENT_VERSION=$2
  NEW_VERSION=$3

  rm -f *.cfg.bkp

  # Backup current toml file
  cp setup.cfg setup.$CURRENT_VERSION.cfg.bkp

  # Updata file with new version
  sed -i '' "s/version = $CURRENT_VERSION/version = $NEW_VERSION/g" setup.cfg

  # Commit new toml file
  git add setup.cfg
  git commit -m "Updating setup file, version $NEW_VERSION"
  git push origin $RELEASE_BRANCH

  # Create release tag
  git tag -a release-$NEW_VERSION -m "Release $NEW_VERSION"

  # Set latest tag
  git tag -d latest
  git push --delete origin latest
  git tag -a latest -m "Release $NEW_VERSION"

  # Push tags
  git push --tags

  # Done!
  print_info "Release $NEW_VERSION is done!"
}
