#!/usr/bin/env bash
set -euo pipefail

# Defaults (override via env or flags)
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-}"
STATE_FILE="${STATE_FILE:-.godelos_cli_state}"

# Actual knowledge endpoints
K_IMPORT_FILE_PATH="/api/knowledge/import/file"
K_IMPORT_URL_PATH="/api/knowledge/import/url"
K_IMPORT_WIKI_PATH="/api/knowledge/import/wikipedia"
K_IMPORT_TEXT_PATH="/api/knowledge/import/text"
K_IMPORT_PROGRESS_TPL="/api/knowledge/import/progress/%s"

K_SEARCH_PATH="/api/knowledge/search"     # GET with query params
K_ADD_PATH="/api/knowledge"               # POST add knowledge
K_REINDEX_PATH="/api/knowledge/reanalyze" # POST

K_GRAPH_STATS_PATH="/api/knowledge/graph/stats"
K_STATS_PATH="/api/knowledge/statistics"
K_EVOLUTION_PATH="/api/knowledge/evolution" # GET timeframe=...
K_RECENT_ENTITIES_PATH="/api/knowledge/entities/recent"
K_EMBEDDINGS_STATS_PATH="/api/knowledge/embeddings/stats"

usage() {
  cat <<'USAGE'
Usage: manage-imports.sh [--base-url URL] [--api-key KEY] <command> [args...]

Global flags:
  --base-url URL     Backend base URL (default: http://localhost:8000)
  --api-key KEY      Bearer token for auth (optional)
  -h, --help         Show help

Generic:
  call METHOD PATH [JSON]         Perform a raw HTTP request (JSON body optional)
  discover [filter]               List endpoints from /openapi.json (filter by substring)

Knowledge import:
  import:file --path FILE [--file-type pdf|txt] [--filename NAME]
  import:url --url URL [--max-depth N] [--follow] [--selectors JSON]
  import:wikipedia --title TITLE [--language en] [--include-refs true|false] [--sections JSON]
  import:text --title TITLE --content "TEXT" [--format plain|markdown]
  import:progress [--id ID]       Show progress for last or provided import id
  import:watch [--id ID]          Poll progress until completion/error

Knowledge ops:
  search --query "text" [--k N]
  add --concept NAME --definition TEXT [--category CAT]
  reindex                        # POST /api/knowledge/reanalyze

Analytics:
  graph:stats
  stats
  evolution [--timeframe 24h]
  entities:recent
  embeddings:stats | vector:status

Examples:
  ./scripts/manage-imports.sh import:file --path docs/paper.pdf --file-type pdf
  ./scripts/manage-imports.sh import:url --url https://example.com --follow --max-depth 1
  ./scripts/manage-imports.sh import:progress
  ./scripts/manage-imports.sh search --query "cognitive transparency" --k 10
  ./scripts/manage-imports.sh evolution --timeframe 7d
USAGE
}

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }
}

init() {
  require curl
  require jq
}

save_state() {
  mkdir -p "$(dirname "$STATE_FILE")"
  printf '%s\n' "$1" > "$STATE_FILE"
}

load_state() {
  [[ -f "$STATE_FILE" ]] && cat "$STATE_FILE" || true
}

json_request() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"

  local url="${BASE_URL}${path}"
  local headers=(-H "Content-Type: application/json")
  [[ -n "${API_KEY}" ]] && headers+=(-H "Authorization: Bearer ${API_KEY}")

  local resp status body
  if [[ -n "${data}" ]]; then
    resp=$(curl -sS -X "${method}" "${headers[@]}" "${url}" -d "${data}" -w $'\n%{http_code}')
  else
    resp=$(curl -sS -X "${method}" "${headers[@]}" "${url}" -w $'\n%{http_code}')
  fi
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"

  if echo "$body" | jq -e . >/dev/null 2>&1; then
    echo "$body" | jq .
  else
    echo "$body"
  fi

  if [[ "$status" -ge 400 ]]; then
    echo "HTTP ${status} from ${method} ${path}" >&2
    exit 1
  fi
}

multipart_request() {
  local path="$1"; shift
  # Remaining args must be -F parts
  local url="${BASE_URL}${path}"
  local args=()
  [[ -n "${API_KEY}" ]] && args+=(-H "Authorization: Bearer ${API_KEY}")
  args+=("${@}")

  # shellcheck disable=SC2068
  local resp status body
  resp=$(curl -sS -X POST ${args[@]} "$url" -w $'\n%{http_code}')
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"

  if echo "$body" | jq -e . >/dev/null 2>&1; then
    echo "$body" | jq .
  else
    echo "$body"
  fi

  if [[ "$status" -ge 400 ]]; then
    echo "HTTP ${status} from POST ${path}" >&2
    exit 1
  fi
}

cmd_call() {
  local method="$1"; shift || { echo "call requires METHOD PATH [JSON]"; exit 1; }
  local path="$1"; shift || { echo "call requires METHOD PATH [JSON]"; exit 1; }
  local body="${1:-}"
  json_request "$method" "$path" "${body}"
}

cmd_discover() {
  local filter="${1:-}"
  local openapi
  openapi=$(curl -sS "${BASE_URL}/openapi.json")
  if [[ -z "$filter" ]]; then
    echo "$openapi" | jq -r '
      .paths | to_entries[]
      | .key as $p
      | .value | to_entries[]
      | "\(.key | ascii_upcase) \($p) [tags: \(.value.tags // [])]"'
  else
    echo "$openapi" | jq -r --arg f "$filter" '
      .paths | to_entries[]
      | select(.key | contains($f))
      | .key as $p
      | .value | to_entries[]
      | "\(.key | ascii_upcase) \($p) [tags: \(.value.tags // [])]"'
  fi
}

cmd_import_file() {
  local path="" file_type="" filename=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --path) path="$2"; shift 2 ;;
      --file-type) file_type="$2"; shift 2 ;;
      --filename) filename="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$path" ]] && { echo "--path is required"; exit 1; }
  [[ ! -f "$path" ]] && { echo "File not found: $path"; exit 1; }

  local parts=(-F "file=@${path}")
  [[ -n "$filename" ]] && parts+=(-F "filename=${filename}")
  [[ -n "$file_type" ]] && parts+=(-F "file_type=${file_type}")

  local out
  out=$(multipart_request "${K_IMPORT_FILE_PATH}" "${parts[@]}")
  # attempt to save import id from response
  local id
  id=$(echo "$out" | jq -r '..|.import_id? // .job_id? // .id? // empty' | head -n1 || true)
  if [[ -n "${id}" && "${id}" != "null" ]]; then
    save_state "$id"
    echo "Saved import id: ${id}" >&2
  fi
}

cmd_import_url() {
  local url="" max_depth=1 follow=false selectors="[]"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --url) url="$2"; shift 2 ;;
      --max-depth) max_depth="$2"; shift 2 ;;
      --follow) follow=true; shift 1 ;;
      --selectors) selectors="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$url" ]] && { echo "--url is required"; exit 1; }
  local payload
  payload=$(jq -nc --arg url "$url" --argjson md "$max_depth" --argjson fl "$follow" --argjson sel "$selectors" \
    '{url: $url, max_depth: $md, follow_links: $fl, content_selectors: $sel}')
  local out id
  out=$(json_request POST "$K_IMPORT_URL_PATH" "$payload")
  id=$(echo "$out" | jq -r '..|.import_id? // .job_id? // .id? // empty' | head -n1 || true)
  if [[ -n "${id}" && "${id}" != "null" ]]; then
    save_state "$id"
    echo "Saved import id: ${id}" >&2
  fi
}

cmd_import_wikipedia() {
  local title="" language="en" include_refs=true sections="[]"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --language) language="$2"; shift 2 ;;
      --include-refs) include_refs="$2"; shift 2 ;;
      --sections) sections="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$title" ]] && { echo "--title is required"; exit 1; }
  local payload
  payload=$(jq -nc --arg t "$title" --arg lang "$language" --argjson ir "$include_refs" --argjson sec "$sections" \
    '{title: $t, language: $lang, include_references: $ir, section_filter: $sec}')
  local out id
  out=$(json_request POST "$K_IMPORT_WIKI_PATH" "$payload")
  id=$(echo "$out" | jq -r '..|.import_id? // .job_id? // .id? // empty' | head -n1 || true)
  if [[ -n "${id}" && "${id}" != "null" ]]; then
    save_state "$id"
    echo "Saved import id: ${id}" >&2
  fi
}

cmd_import_text() {
  local title="Manual Text Input" content="" format="plain"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --content) content="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$content" ]] && { echo "--content is required"; exit 1; }
  local payload
  payload=$(jq -nc --arg title "$title" --arg content "$content" --arg fmt "$format" \
    '{title: $title, content: $content, format_type: $fmt}')
  local out id
  out=$(json_request POST "$K_IMPORT_TEXT_PATH" "$payload")
  id=$(echo "$out" | jq -r '..|.import_id? // .job_id? // .id? // empty' | head -n1 || true)
  if [[ -n "${id}" && "${id}" != "null" ]]; then
    save_state "$id"
    echo "Saved import id: ${id}" >&2
  fi
}

cmd_import_progress() {
  local id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id|--job) id="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$id" ]] && id="$(load_state)"
  [[ -z "$id" ]] && { echo "No --id provided and no saved id"; exit 1; }
  local path
  path=$(printf "$K_IMPORT_PROGRESS_TPL" "$id")
  json_request GET "$path"
}

cmd_import_watch() {
  local id=""; local interval=2
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id|--job) id="$2"; shift 2 ;;
      --interval) interval="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$id" ]] && id="$(load_state)"
  [[ -z "$id" ]] && { echo "No --id provided and no saved id"; exit 1; }
  echo "Watching progress for $id (every ${interval}s)..." >&2
  while true; do
    local out status
    out=$(cmd_import_progress --id "$id" || true)
    echo "$out" | jq .
    status=$(echo "$out" | jq -r '.status // .data.status // ""' || true)
    case "$status" in
      completed|error|not_found) break;;
    esac
    sleep "$interval"
  done
}

cmd_search() {
  local query="" k="5"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --query) query="$2"; shift 2 ;;
      --k) k="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$query" ]] && { echo "--query is required"; exit 1; }
  local path
  path="${K_SEARCH_PATH}?$(jq -rn --arg q "$query" --arg k "$k" '"query="+@uri($q)+"&k="+$k')"
  json_request GET "$path"
}

cmd_add() {
  local concept="" definition="" category="general"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --concept) concept="$2"; shift 2 ;;
      --definition|--content) definition="$2"; shift 2 ;;
      --category) category="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  [[ -z "$concept" || -z "$definition" ]] && { echo "--concept and --definition are required"; exit 1; }
  local payload
  payload=$(jq -nc --arg c "$concept" --arg d "$definition" --arg cat "$category" '{concept: $c, definition: $d, category: $cat}')
  json_request POST "$K_ADD_PATH" "$payload"
}

cmd_reindex() {
  json_request POST "$K_REINDEX_PATH" '{}'
}

cmd_graph_stats() { json_request GET "$K_GRAPH_STATS_PATH"; }
cmd_stats() { json_request GET "$K_STATS_PATH"; }

cmd_evolution() {
  local timeframe="24h"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --timeframe) timeframe="$2"; shift 2 ;;
      *) echo "Unknown arg: $1"; exit 1 ;;
    esac
  done
  local path
  path="${K_EVOLUTION_PATH}?$(jq -rn --arg tf "$timeframe" '"timeframe="+@uri($tf)')"
  json_request GET "$path"
}

cmd_recent_entities() { json_request GET "$K_RECENT_ENTITIES_PATH"; }
cmd_embeddings_stats() { json_request GET "$K_EMBEDDINGS_STATS_PATH"; }

# Parse globals
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${#}" -eq 0 ]]; then
  usage; exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --api-key) API_KEY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) break ;;
  esac
done

init

cmd="${1:-}"; shift || true
case "$cmd" in
  call) cmd_call "$@";;
  discover) cmd_discover "${1:-}";;
  import:file) cmd_import_file "$@";;
  import:url) cmd_import_url "$@";;
  import:wikipedia) cmd_import_wikipedia "$@";;
  import:text) cmd_import_text "$@";;
  import:progress) cmd_import_progress "$@";;
  import:watch) cmd_import_watch "$@";;
  search) cmd_search "$@";;
  add) cmd_add "$@";;
  reindex) cmd_reindex "$@";;
  graph:stats) cmd_graph_stats ;;
  stats) cmd_stats ;;
  evolution) cmd_evolution "$@";;
  entities:recent) cmd_recent_entities ;;
  embeddings:stats|vector:status) cmd_embeddings_stats ;;
  *) echo "Unknown command: $cmd"; usage; exit 1;;
esac
