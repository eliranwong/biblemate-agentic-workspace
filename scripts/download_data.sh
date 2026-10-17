#!/usr/bin/env bash
# ==============================================================================
# BibleMate Database Download & Setup Script
# Downloads data.zip from MEGA and unpacks to ~/biblemate/data
# ==============================================================================

set -e

MEGA_URL="https://mega.nz/file/SaBkhRZA#H10dm7nCbShAO1xHo2dWhOWaX3eda8Y-R83v225jBYw"
TARGET_DIR="${HOME}/biblemate"
ZIP_FILE="${TARGET_DIR}/data.zip"

echo "=== BibleMate Local Database Setup ==="

# 1. Make sure biblemate directory exists in home directory
mkdir -p "${TARGET_DIR}"

# 2. Check if data directory already exists
if [ -d "${TARGET_DIR}/data" ] && [ "$(ls -A "${TARGET_DIR}/data" 2>/dev/null)" ]; then
    echo "Notice: '${TARGET_DIR}/data' already exists and is not empty."
    read -r -p "Do you want to overwrite / unpack again? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            ;;
        *)
            echo "Skipping download and extraction. Setup aborted."
            exit 0
            ;;
    esac
fi

# 3. Locate or download data.zip
if [ ! -f "${ZIP_FILE}" ]; then
    if [ -f "${HOME}/Downloads/data.zip" ]; then
        echo "Found data.zip in ~/Downloads. Copying to ${TARGET_DIR} ..."
        cp "${HOME}/Downloads/data.zip" "${ZIP_FILE}"
    elif [ -f "./data.zip" ]; then
        echo "Found data.zip in current directory. Copying to ${TARGET_DIR} ..."
        cp "./data.zip" "${ZIP_FILE}"
    elif command -v megatools >/dev/null 2>&1; then
        echo "Downloading data.zip using megatools ..."
        megatools dl "${MEGA_URL}" --path "${TARGET_DIR}/"
    elif command -v mega-get >/dev/null 2>&1; then
        echo "Downloading data.zip using mega-cmd ..."
        mega-get "${MEGA_URL}" "${TARGET_DIR}/"
    else
        echo ""
        echo "ERROR: Could not find 'data.zip' or an automated MEGA downloader."
        echo ""
        echo "Please choose one of the following methods to obtain the file:"
        echo "  Method 1 (Command Line): Install megatools and run this script again:"
        echo "    - macOS:   brew install megatools"
        echo "    - Linux:   sudo apt install megatools"
        echo ""
        echo "  Method 2 (Browser / QR Code):"
        echo "    - URL:     ${MEGA_URL}"
        echo "    - QR Code: docs/download_data_qr_code.png"
        echo "    - Save the downloaded 'data.zip' to ~/Downloads/ or ${TARGET_DIR}/"
        echo "    - Then re-run this script."
        echo ""
        exit 1
    fi
fi

# 4. Unzip into ~/biblemate (unpacked directory will be ~/biblemate/data)
echo "Unpacking data.zip into ${TARGET_DIR} ..."
unzip -q -o "${ZIP_FILE}" -d "${TARGET_DIR}"

# 5. Verify and clean up
if [ -d "${TARGET_DIR}/data" ]; then
    echo "Success! Database files are ready in ${TARGET_DIR}/data"
    rm -f "${ZIP_FILE}"
    echo "Removed temporary archive: ${ZIP_FILE}"
else
    echo "Warning: Extraction finished, but '${TARGET_DIR}/data' was not found."
fi
