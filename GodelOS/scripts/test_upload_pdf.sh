#!/usr/bin/env bash
set -euo pipefail

# Test script: uploads a PDF (or supported file) to the backend import endpoint
# Usage: ./scripts/test_upload_pdf.sh /path/to/file.pdf [BASE_URL]

BASE_URL=${2:-${BASE_URL:-http://localhost:8000}}
FILE=${1:-}

if [ -z "$FILE" ]; then
  echo "Usage: $0 /path/to/file.pdf [BASE_URL]"
  exit 2
fi

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE"
  exit 2
fi

filename=$(basename "$FILE")
ext="${filename##*.}"
# normalize extension to lowercase
ext_lower=$(echo "$ext" | tr 'A-Z' 'a-z')

case "$ext_lower" in
  pdf) file_type=pdf ;;
  txt) file_type=txt ;;
  docx) file_type=docx ;;
  json) file_type=json ;;
  csv) file_type=csv ;;
  *)
    echo "Warning: unknown extension '$ext_lower' - defaulting to 'pdf' file_type"
    file_type=pdf ;;
esac

echo "Uploading '$FILE' to $BASE_URL as file_type=$file_type"

TMP_RSP=$(mktemp)
curl -s -w "\nHTTP_CODE:%{http_code}\n" -X POST \
  -F "file=@${FILE};filename=${filename}" \
  -F "filename=${filename}" \
  -F "file_type=${file_type}" \
  "$BASE_URL/api/knowledge/import/file" -o "$TMP_RSP" || true

echo "Server response:"
cat "$TMP_RSP"

# Try to pretty-print JSON if jq is available
if command -v jq >/dev/null 2>&1; then
  echo
  echo "Parsed JSON:"
  jq . "$TMP_RSP" || true
fi

IMPORT_ID=$(jq -r '.import_id // empty' "$TMP_RSP" 2>/dev/null || true)
if [ -n "$IMPORT_ID" ]; then
  echo
  echo "Import started with id: $IMPORT_ID"
  echo "Polling progress endpoint for up to 60s..."
  for i in $(seq 1 60); do
    sleep 1
    PROG=$(curl -s "$BASE_URL/api/knowledge/import/progress/${IMPORT_ID}" || true)
    if [ -n "$PROG" ]; then
      if command -v jq >/dev/null 2>&1; then
        echo "[$i] "$(echo "$PROG" | jq -c '.')
      else
        echo "[$i] $PROG"
      fi
      STATUS=$(echo "$PROG" | jq -r '.status // empty' 2>/dev/null || true)
      if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo "Finished with status: $STATUS"
        break
      fi
    fi
  done
else
  echo "No import_id returned; check response above for errors."
fi

rm -f "$TMP_RSP"
exit 0
