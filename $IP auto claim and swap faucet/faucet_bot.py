import logging
import requests
from web3 import Web3
import time
import config
from web3.exceptions import ContractLogicError
import concurrent.futures
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rpc_connection(url):
    try:
        response = requests.post(url, json={"jsonrpc": "2.0", "method": "net_version", "params": [], "id": 1})
        logger.info(f"RPC Response: {response.json()}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error connecting to RPC: {e}")
        return None

def setup_web3():
    w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    accounts = [w3.eth.account.from_key(pk) for pk in config.PRIVATE_KEYS]
    return w3, accounts

def get_nonce(w3, address):
    return w3.eth.get_transaction_count(address, 'pending')

def get_token_balance(w3, token_address, account_address):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=config.SUDT_ABI)
    balance = token_contract.functions.balanceOf(account_address).call()
    return balance

def claim_token(w3, account, token, address, nonce):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Mengklaim {token} untuk {account.address}... (Percobaan {attempt + 1})")
            token_contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=config.SUDT_ABI)

            balance_before = get_token_balance(w3, address, account.address)
            logger.info(f"Saldo {token} sebelum klaim: {balance_before}")

            gas_price = w3.eth.gas_price
            gas_price_multiplier = 1.5 + (0.2 * attempt)

            tx = token_contract.functions.claim().build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': int(gas_price * gas_price_multiplier)
            })

            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Transaksi {token} terkirim untuk {account.address}. Hash: {tx_hash.hex()}")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt['status'] == 1:
                balance_after = get_token_balance(w3, address, account.address)
                if balance_after > balance_before:
                    logger.info(f"Klaim {token} berhasil untuk {account.address}! Saldo bertambah {balance_after - balance_before}")
                    return True
                else:
                    logger.warning(f"Klaim {token} berhasil, tapi saldo tidak bertambah untuk {account.address}.")
            else:
                logger.warning(f"Klaim {token} gagal untuk {account.address}. Status: {receipt['status']}")

            time.sleep(2 * (attempt + 1))  # Exponential backoff

        except ContractLogicError as e:
            logger.error(f"Contract logic error saat mengklaim {token} untuk {account.address}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saat mengklaim {token} untuk {account.address}: {e}")
            time.sleep(2 * (attempt + 1))

    logger.error(f"Gagal mengklaim {token} untuk {account.address} setelah {max_retries} percobaan.")
    return False

def batch_claim_all(w3, accounts):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        nonce_dict = defaultdict(int)

        for account in accounts:
            nonce = get_nonce(w3, account.address)
            nonce_dict[account.address] = nonce
            for token, address in config.TOKEN_ADDRESSES.items():
                futures.append(executor.submit(claim_token, w3, account, token, address, nonce_dict[account.address]))
                nonce_dict[account.address] += 1

        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return all(results)

def claim_faucet(w3, accounts):
    while True:
        batch_claim_all(w3, accounts)
        logger.info("Satu putaran klaim selesai, melanjutkan ke putaran berikutnya...")

def main():
    logger.info("Checking RPC connection...")
    rpc_response = check_rpc_connection(config.RPC_URL)
    if rpc_response:
        logger.info(f"RPC connection successful. Network ID: {rpc_response.get('result')}")
        w3, accounts = setup_web3()
        chain_id = w3.eth.chain_id
        logger.info(f"Terhubung ke jaringan: {chain_id}")
        for i, account in enumerate(accounts):
            logger.info(f"Menggunakan alamat {i+1}: {account.address}")
        claim_faucet(w3, accounts)
    else:
        logger.error("Failed to connect to RPC. Please check your RPC URL and network connection.")

if __name__ == "__main__":
    main()