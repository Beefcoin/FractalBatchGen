#!/usr/bin/env bash
set -e

OUTPUT_DIR="generated/test_all_algorithms"
REFERENCE_FILE="generation_checksums.sha256"
CURRENT_FILE="generation_checksums_current.sha256"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: $OUTPUT_DIR does not exist."
    echo "Run the test generation first:"
    echo "  docker compose run --rm agglomerate-generation ./generate.sh config/genTest_all.json"
    exit 1
fi

if [ ! -f "$REFERENCE_FILE" ]; then
    echo "Error: Reference checksum file '$REFERENCE_FILE' was not found."
    echo
    echo "Create it once from the reference generation with:"
    echo
    echo "  find $OUTPUT_DIR \\"
    echo "      -type f -name \"*.csv\" \\"
    echo "      ! -path \"*/analysis/*\" \\"
    echo "      -print0 \\"
    echo "      | sort -z \\"
    echo "      | xargs -0 sha256sum \\"
    echo "      > $REFERENCE_FILE"
    exit 1
fi

echo "Generating SHA-256 checksums..."

find "$OUTPUT_DIR" \
    -type f -name "*.csv" \
    ! -path "*/analysis/*" \
    -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > "$CURRENT_FILE"

echo
echo "Comparing generated files with reference checksums..."
echo

if diff -u "$REFERENCE_FILE" "$CURRENT_FILE"; then
    echo
    echo "All generated agglomerates are identical to the reference files."
    rm "$CURRENT_FILE"
    exit 0
else
    echo
    echo "WARNING: Generated agglomerates differ from the reference files."
    echo "Current checksums are stored in: $CURRENT_FILE"
    exit 1
fi