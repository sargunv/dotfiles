install_if_missing() {
  command_name="$1"
  install_command="$2"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    sh -c "$install_command"
  fi
}
