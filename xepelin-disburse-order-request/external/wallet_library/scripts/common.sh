source scripts/colors.sh

print_error() {
  echo "${COLOR_RED}$1${COLOR_RESET}"
}

print_warning() {
  echo "${COLOR_YELLOW}$1${COLOR_RESET}"
}

print_info() {
  echo "${COLOR_GREEN}$1${COLOR_RESET}"
}
