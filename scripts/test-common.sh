#!/usr/bin/env bash
# Common functions for test scripts

# Colors
readonly COLOR_RESET='\033[0m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_DIM='\033[2m'
readonly COLOR_BLUE='\033[34m'
readonly COLOR_CYAN='\033[36m'
readonly COLOR_GREEN='\033[32m'
readonly COLOR_YELLOW='\033[33m'
readonly COLOR_GRAY='\033[90m'

# Print a major section header
print_header() {
    local title="$1"
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}  $title${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════${COLOR_RESET}"
    echo ""
}

# Print a test case header
print_test() {
    local test_num="$1"
    local description="$2"
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━ TEST $test_num: $description${COLOR_RESET}"
    echo ""
}

# Print script informational message
print_info() {
    local message="$1"
    echo -e "${COLOR_DIM}${COLOR_GRAY}[script] $message${COLOR_RESET}"
}

# Print success message
print_success() {
    local message="$1"
    echo -e "${COLOR_GREEN}✓ $message${COLOR_RESET}"
}

# Print expected failure message (dimmed)
print_expected_failure() {
    local message="$1"
    echo -e "${COLOR_DIM}${COLOR_GRAY}✓ $message${COLOR_RESET}"
}

# Print separator (default gray, or custom color)
print_separator() {
    local color="${1:-${COLOR_GRAY}}"
    echo -e "${COLOR_DIM}${color}─────────────────────────────────────${COLOR_RESET}"
}

# Indicate CLI command is starting
print_cli_start() {
    local command="$1"
    echo -e "${COLOR_DIM}Running: $command${COLOR_RESET}"
    print_separator
}

# Indicate CLI output has ended
print_cli_end() {
    print_separator
}

# Print a key-value pair
print_keyval() {
    local key="$1"
    local value="$2"
    echo -e "${COLOR_DIM}  $key: ${COLOR_RESET}$value"
}
