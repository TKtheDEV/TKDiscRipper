#!/bin/bash

set -euo pipefail

# Track current step for error reporting
CURRENT_STEP="Starting script"

# Error handler
trap 'echo -e "\n❌ Error during: $CURRENT_STEP\n"; exit 1' ERR

# --- Functions ---

log() {
    echo -e "\n🔹 $1"
}

install_dependencies() {
    CURRENT_STEP="Installing system dependencies"
    log "Installing base dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 python3-venv python3-pip flac abcde flatpak \
        build-essential pkg-config libc6-dev libssl-dev \
        libexpat1-dev libavcodec-dev libgl1-mesa-dev \
        qtbase5-dev zlib1g-dev
}

install_lact() {
    CURRENT_STEP="Installing LACT"
    log "Installing LACT..."

    local REPO="ilya-zlobintsev/LACT"
    local API_URL="https://api.github.com/repos/$REPO/releases/latest"

    if ! command -v apt &> /dev/null; then
        echo "This script is intended for Debian-based systems (Ubuntu, Debian, etc.)"
        return 1
    fi

    . /etc/os-release
    DISTRO=$ID
    VERSION_ID=${VERSION_ID//\"/}
    VERSION_SIMPLE=$(echo "$VERSION_ID" | tr -d '.')

    echo "Detected system: $DISTRO $VERSION_ID"

    if [[ "$DISTRO" != "ubuntu" && "$DISTRO" != "debian" ]]; then
        echo "Unsupported distro: $DISTRO"
        return 1
    fi

    RELEASE_JSON=$(curl -s "$API_URL")
    DEB_URLS=$(echo "$RELEASE_JSON" | grep "browser_download_url" | grep "\.deb" | cut -d '"' -f 4)

    MATCHED_URL=""
    for url in $DEB_URLS; do
        if [[ "$url" == *"$DISTRO-$VERSION_SIMPLE.deb" ]]; then
            MATCHED_URL="$url"
            break
        fi
    done

    if [ -z "$MATCHED_URL" ]; then
        log "Exact match not found. Looking for closest match..."
        MATCHED_URL=$(echo "$DEB_URLS" | grep "$DISTRO" | sort -V | tail -n 1)
    fi

    if [ -z "$MATCHED_URL" ]; then
        echo "No suitable .deb package found."
        return 1
    fi

    FILENAME=$(basename "$MATCHED_URL")
    curl -LO "$MATCHED_URL"
    sudo apt install -y "./$FILENAME"
    rm "$FILENAME"

    log "LACT installed successfully."
}

install_makemkv() {
    CURRENT_STEP="Installing MakeMKV from forum-sourced URLs"
    log "Fetching latest MakeMKV download links from forum..."

    FORUM_URL="https://forum.makemkv.com/forum/viewtopic.php?t=224"
    PAGE_CONTENT=$(curl -s "$FORUM_URL")

    # Extract the latest OSS and BIN URLs
    OSS_URL=$(echo "$PAGE_CONTENT" | grep -oP 'https://www.makemkv.com/download/makemkv-oss-[0-9.]+\.tar\.gz' | head -n 1)
    BIN_URL=$(echo "$PAGE_CONTENT" | grep -oP 'https://www.makemkv.com/download/makemkv-bin-[0-9.]+\.tar\.gz' | head -n 1)

    if [[ -z "$OSS_URL" || -z "$BIN_URL" ]]; then
        echo "❌ Failed to extract MakeMKV download URLs."
        return 1
    fi

    # Extract version number from OSS URL
    VERSION=$(echo "$OSS_URL" | grep -oP '[0-9]+\.[0-9]+\.[0-9]+')

    log "Found MakeMKV version: $VERSION"
    log "Downloading OSS and BIN tarballs..."

    curl -LO "$OSS_URL"
    curl -LO "$BIN_URL"

    # Extract archives
    tar xzf "makemkv-oss-$VERSION.tar.gz"
    tar xzf "makemkv-bin-$VERSION.tar.gz"

    # Compile OSS
    pushd "makemkv-oss-$VERSION"
    ./configure
    make
    sudo make install
    popd

    # Compile BIN
    pushd "makemkv-bin-$VERSION"
    make
    sudo make install
    popd

    rm -rf "makemkv-oss-$VERSION" "makemkv-bin-$VERSION"
    rm "makemkv-oss-$VERSION.tar.gz" "makemkv-bin-$VERSION.tar.gz"

    log "✅ MakeMKV $VERSION installed successfully."
}

install_makemkv_key() {
    CURRENT_STEP="Fetching MakeMKV beta key from cable.ayra.ch"
    log "Fetching MakeMKV beta key..."

    BETA_KEY=$(curl -s "https://cable.ayra.ch/makemkv/api.php?raw")

    if [[ -z "$BETA_KEY" ]]; then
        echo "❌ Failed to fetch a valid MakeMKV beta key."
        return 1
    fi

    log "Fetched beta key: $BETA_KEY"

    # Ensure MakeMKV config dir exists
    mkdir -p ~/.MakeMKV
    CONFIG_FILE=~/.MakeMKV/settings.conf

    # Add or update the app_Key
    if grep -q "^app_Key" "$CONFIG_FILE" 2>/dev/null; then
        sed -i "s|^app_Key.*|app_Key = $BETA_KEY|" "$CONFIG_FILE"
    else
        echo "app_Key = $BETA_KEY" >> "$CONFIG_FILE"
    fi

    log "Beta key saved to $CONFIG_FILE"
}


# --- Main ---

log "Beginning full setup process..."

install_dependencies
install_lact
install_makemkv
install_makemkv_key


log "✅ Setup complete!"