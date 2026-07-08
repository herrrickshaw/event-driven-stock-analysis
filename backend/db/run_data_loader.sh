#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Event-Driven Stock Analysis - Historical Data Loader Scripts
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${SCRIPT_DIR}/load_historical_data.log"
PROGRESS_DIR="${SCRIPT_DIR}/data/progress"

# ═════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_postgres() {
    if ! command -v pg_isready &> /dev/null; then
        log_warning "PostgreSQL client tools not found"
        return 1
    fi

    if pg_isready -h localhost -p 5432 &> /dev/null; then
        log_success "PostgreSQL is running"
        return 0
    else
        log_error "PostgreSQL is not running"
        return 1
    fi
}

check_python_deps() {
    local missing=()

    for package in yfinance psycopg2 pandas tqdm; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing+=("$package")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing Python dependencies: ${missing[*]}"
        return 1
    fi

    log_success "All Python dependencies installed"
    return 0
}

get_progress_summary() {
    local market=$1
    local progress_file="${PROGRESS_DIR}/${market}_progress.json"

    if [ -f "$progress_file" ]; then
        python3 << EOF
import json
with open('$progress_file') as f:
    data = json.load(f)
    completed = data.get('completed_stocks', 0)
    total = data.get('total_stocks', 0)
    records = data.get('inserted_records', 0)
    print(f"Progress: {completed}/{total} stocks, {records:,} records")
EOF
    else
        echo "No progress file found"
    fi
}

# ═════════════════════════════════════════════════════════════════════════════
# LOAD COMMANDS
# ═════════════════════════════════════════════════════════════════════════════

load_single_market() {
    local market=$1
    local workers=${2:-4}

    log_info "Loading ${market} market with ${workers} workers..."

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets "$market" \
        --workers "$workers" \
        --batch-size 500 \
        --log-level INFO
}

load_multiple_markets() {
    local markets=$@

    log_info "Loading markets: ${markets}"

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets $markets \
        --workers 6 \
        --batch-size 500 \
        --log-level INFO
}

load_all_markets() {
    local workers=${1:-4}

    log_info "Loading ALL 8 markets with ${workers} workers..."
    log_warning "This will take approximately 20-24 hours"

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets india usa europe japan korea uk brazil china \
        --workers "$workers" \
        --batch-size 500 \
        --log-level INFO
}

resume_load() {
    local market=$1

    log_info "Resuming load for ${market} from checkpoint..."

    if [ ! -f "${PROGRESS_DIR}/${market}_progress.json" ]; then
        log_error "No checkpoint found for ${market}"
        return 1
    fi

    get_progress_summary "$market"

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets "$market" \
        --resume \
        --workers 4 \
        --log-level INFO
}

load_incremental() {
    local markets=$@

    log_info "Loading only missing dates for: ${markets}"

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets $markets \
        --only-missing \
        --workers 6 \
        --log-level INFO
}

dry_run() {
    local markets=${1:-india}

    log_info "DRY RUN: Testing ${markets} without database writes..."

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --markets $markets \
        --dry-run \
        --workers 2 \
        --log-level DEBUG
}

# ═════════════════════════════════════════════════════════════════════════════
# UTILITY COMMANDS
# ═════════════════════════════════════════════════════════════════════════════

show_progress() {
    log_info "Showing progress for all markets..."

    for market in india usa europe japan korea uk brazil china; do
        echo -n "  $market: "
        get_progress_summary "$market"
    done
}

cleanup_progress() {
    log_warning "Cleaning progress files (will restart from beginning)..."

    if [ -d "$PROGRESS_DIR" ]; then
        rm -f "$PROGRESS_DIR"/*.json
        log_success "Progress files deleted"
    fi
}

tail_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        log_error "Log file not found: $LOG_FILE"
        return 1
    fi

    tail -f "$LOG_FILE"
}

validate_database() {
    log_info "Validating database schema..."

    python3 "${SCRIPT_DIR}/load_historical_data.py" \
        --validate-only \
        --log-level INFO
}

# ═════════════════════════════════════════════════════════════════════════════
# SETUP COMMANDS
# ═════════════════════════════════════════════════════════════════════════════

setup() {
    log_info "Setting up event-driven stock analysis data loader..."

    # Check PostgreSQL
    if ! check_postgres; then
        log_error "Please start PostgreSQL and try again"
        log_info "  macOS with Homebrew: brew services start postgresql@15"
        log_info "  Docker: docker run -d -p 5432:5432 postgres:15"
        return 1
    fi

    # Check Python dependencies
    if ! check_python_deps; then
        log_info "Installing missing dependencies..."
        pip3 install -r "${SCRIPT_DIR}/requirements.txt"

        if ! check_python_deps; then
            log_error "Failed to install dependencies"
            return 1
        fi
    fi

    # Create directories
    mkdir -p "$PROGRESS_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"

    log_success "Setup complete!"
    log_info "Ready to load data. Run: $0 help"
}

# ═════════════════════════════════════════════════════════════════════════════
# HELP & MAIN
# ═════════════════════════════════════════════════════════════════════════════

show_help() {
    cat << EOF
${BLUE}╔════════════════════════════════════════════════════════════════╗
║  Historical OHLCV Data Loader for Event-Driven Stock Analysis   ║
╚════════════════════════════════════════════════════════════════╝${NC}

${GREEN}SETUP${NC}
  setup                    Initialize database and dependencies

${GREEN}LOAD COMMANDS${NC}
  load <market>            Load single market (india|usa|europe|...)
  load <market1> <market2> Load multiple markets
  load-all                 Load all 8 markets (20+ hours)
  resume <market>          Resume interrupted load from checkpoint
  incremental              Load only missing dates for all markets

${GREEN}TESTING${NC}
  dry-run [market]         Test without database writes (india by default)

${GREEN}MONITORING${NC}
  progress                 Show load progress for all markets
  tail-logs                Follow log file in real-time
  cleanup                  Delete progress files (restart from beginning)

${GREEN}UTILITY${NC}
  validate                 Validate database schema
  help                     Show this message

${BLUE}EXAMPLES${NC}

  # First time setup
  $0 setup

  # Test with India market (no DB writes)
  $0 dry-run india

  # Load India market
  $0 load india

  # Load India and USA in parallel
  $0 load india usa

  # Resume interrupted load
  $0 resume usa

  # Update with only missing dates
  $0 incremental

  # Monitor progress
  $0 progress
  $0 tail-logs

${BLUE}PERFORMANCE NOTES${NC}

  Worker threads (default 4):
    - 2-4   workers: Low bandwidth connections
    - 6-8   workers: Standard (recommended)
    - 12-16 workers: High bandwidth servers

  Expected throughput: 100K-300K records/hour depending on connection

  All 8 markets (825K records) typically takes 20-24 hours

EOF
}

main() {
    local command=${1:-help}

    case "$command" in
        setup)
            setup
            ;;
        load)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 load <market> [market2] [market3] ..."
                exit 1
            fi
            shift
            load_multiple_markets "$@"
            ;;
        load-all)
            load_all_markets "${2:-6}"
            ;;
        resume)
            if [ $# -ne 2 ]; then
                log_error "Usage: $0 resume <market>"
                exit 1
            fi
            resume_load "$2"
            ;;
        incremental)
            load_incremental india usa europe japan korea uk brazil china
            ;;
        dry-run)
            dry_run "${2:-india}"
            ;;
        progress)
            show_progress
            ;;
        tail-logs)
            tail_logs
            ;;
        cleanup)
            cleanup_progress
            ;;
        validate)
            validate_database
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
