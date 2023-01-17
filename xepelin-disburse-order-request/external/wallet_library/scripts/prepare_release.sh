source scripts/common.sh
source scripts/execute_release.sh

RELEASE_BRANCH=master

check_branch() {
    CURRENT_BRANCH=$(git branch | sed -rn 's/\* (.*)/\1/p')

    if [ "$CURRENT_BRANCH" != "$RELEASE_BRANCH" ]; then
        print_error "Module can only be released from branch '${RELEASE_BRANCH}'."

        exit 1
    else
        print_info "We're on the right branch..."
    fi
}

check_uncommited_changes() {
    CHANGED_FILES=$(git status --porcelain | wc -l)

    if [ $CHANGED_FILES -gt 0 ]; then
        print_error "Module cannot be released with uncommited changes."

        exit 1
    else
        print_info "No uncommited changes..."
    fi
}

run_tests() {
    print_info "Running tests..."

    pytest

    if [ $? -ne 0 ]; then
        print_error "One or more tests failed."

        exit 1
    else
        print_info "Tests OK..."
    fi
}

VERSION=$(cat setup.cfg | grep version | sed -rn 's/version = ([0-9]+\.[0-9]+\.[0-9]+)/\1/p')

PATCH_VERSION=$(echo $VERSION | sed -rn 's/.*\..*\.(.*)/\1/p')
MINOR_VERSION=$(echo $VERSION | sed -rn 's/.*\.(.*)\..*/\1/p')
MAYOR_VERSION=$(echo $VERSION | sed -rn 's/(.*)\..*\..*/\1/p')

bump_patch() {
    tmp=$(($PATCH_VERSION + 1))

    NEW_VERSION="$MAYOR_VERSION.$MINOR_VERSION.$tmp"
}

bump_minor() {
    tmp=$(($MINOR_VERSION + 1))

    NEW_VERSION="$MAYOR_VERSION.$tmp.0"
}

bump_mayor() {
    tmp=$(($MAYOR_VERSION + 1))

    NEW_VERSION="$tmp.0.0"
}

select_bump() {
    select BUMP in "patch" "minor" "mayor" "cancel"; do
        case $BUMP in
        patch)
            bump_patch
            break
            ;;
        minor)
            bump_minor
            break
            ;;
        mayor)
            bump_mayor
            break
            ;;
        cancel) exit 0 ;;
        esac
    done
}

should_proceed() {
    print_info "Continue?"

    select YN in "Yes" "No"; do
        case $YN in
        Yes)
            execute_release $RELEASE_BRANCH $VERSION $NEW_VERSION
            break
            ;;
        No)
            exit 0
            ;;
        esac
    done
}

check_branch

check_uncommited_changes

run_tests

print_info "Select which version type to bump:"

select_bump

print_warning "Current version: $VERSION"
print_info "New version: $NEW_VERSION"

should_proceed
