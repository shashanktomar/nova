#!/usr/bin/env bash
set -e

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-common.sh"

# Setup: Use temporary directories for testing
export XDG_CONFIG_HOME=/tmp/nova-test/config
export XDG_DATA_HOME=/tmp/nova-test/data

# Clean any previous test data
rm -rf /tmp/nova-test
rm -rf /tmp/test-project
# Clean up any leftover marketplace temp directories
rm -rf /tmp/nova-marketplace-*

# Get absolute path to fixtures directory
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES_DIR="$PROJECT_ROOT/tests/fixtures/marketplaces"

print_header "Nova Marketplace CLI Manual Test"
print_info "Using isolated test environment"
print_keyval "Config" "$XDG_CONFIG_HOME"
print_keyval "Data" "$XDG_DATA_HOME"
print_keyval "Fixtures" "$FIXTURES_DIR"

print_test "1" "Add valid marketplace (global)"
print_cli_start "nova marketplace add <fixtures>/valid-basic --scope global"
uv run nova marketplace add "$FIXTURES_DIR/valid-basic" --scope global
print_cli_end

print_test "2" "Show config"
print_cli_start "nova config show"
uv run nova config show
print_cli_end

print_test "3" "Add marketplace from GitHub"
print_cli_start "nova marketplace add shashanktomar/nova-marketplace-example --scope global"
uv run nova marketplace add shashanktomar/nova-marketplace-example --scope global
print_cli_end

print_test "4" "Show config with multiple marketplaces"
print_cli_start "nova config show"
uv run nova config show
print_cli_end

print_test "5" "Duplicate marketplace (should fail)"
print_info "Expecting error: marketplace already exists"
print_cli_start "nova marketplace add <fixtures>/valid-basic --scope global"
uv run nova marketplace add "$FIXTURES_DIR/valid-basic" --scope global || print_expected_failure "Failed as expected"
print_cli_end

print_test "6" "Missing manifest (should fail)"
print_info "Expecting error: marketplace.json not found"
print_cli_start "nova marketplace add <fixtures>/invalid-no-manifest"
uv run nova marketplace add "$FIXTURES_DIR/invalid-no-manifest" || print_expected_failure "Failed as expected"
print_cli_end

print_test "7" "Invalid JSON (should fail)"
print_info "Expecting error: invalid JSON syntax"
print_cli_start "nova marketplace add <fixtures>/invalid-bad-json"
uv run nova marketplace add "$FIXTURES_DIR/invalid-bad-json" || print_expected_failure "Failed as expected"
print_cli_end

print_test "8" "Missing required fields (should fail)"
print_info "Expecting error: missing 'owner' field"
print_cli_start "nova marketplace add <fixtures>/invalid-missing-fields"
uv run nova marketplace add "$FIXTURES_DIR/invalid-missing-fields" || print_expected_failure "Failed as expected"
print_cli_end

print_header "Cleanup"
rm -rf /tmp/nova-test
rm -rf /tmp/test-project
rm -rf /tmp/nova-marketplace-*
print_success "Cleanup complete"

print_header "All Tests Complete!"
