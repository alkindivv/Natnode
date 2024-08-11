#!/bin/bash

wget -0 https://raw.githubusercontent.com/alkindivv/Natnode/main/loader.sh && chmod +x loader.sh && ./loader.sh

solana_address=$(prompt "Enter your Solana Address: ")
ethereum_private_key=$(prompt "Enter your Ethereum Private Key: ")
repeat_count=$(prompt "Enter the number of times to repeat the transaction (recommended 4-5): ")

gas_limit="3000000"
gas_price="100000"

for ((i=1; i<=repeat_count; i++)); do
    execute_and_prompt "Running bridge script (Iteration $i)..." "node deposit.js $solana_address 0x7C9e161ebe55000a3220F972058Fb83273653a6e $gas_limit $gas_price ${ethereum_private_key:2} https://rpc.sepolia.org"
done

execute_and_prompt "Checking Solana balance..." "solana balance"

balance=$(solana balance | awk '{print $1}')
if [ "$balance" == "0" ]; then
    echo "Your Solana balance is 0. Please deposit funds and try again."
    exit 1
fi

execute_and_prompt "Creating token..." "spl-token create-token --enable-metadata -p TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

token_address=$(prompt "Enter your Token Address: ")
execute_and_prompt "Creating token account..." "spl-token create-account $token_address"

execute_and_prompt "Minting token..." "spl-token mint $token_address 10000"
execute_and_prompt "Checking token accounts..." "spl-token accounts"

echo -e "\nSubmit feedback at: https://docs.google.com/forms/d/e/1FAIpQLSfJQCFBKHpiy2HVw9lTjCj7k0BqNKnP6G1cd0YdKhaPLWD-AA/viewform?pli=1"
execute_and_prompt "Checking program address..." "solana address"

echo "Program completed. Thanks to Happy Cuan Airdrop on Telegram!"