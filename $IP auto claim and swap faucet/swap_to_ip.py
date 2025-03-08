import logging
import time
from web3 import Web3
import config
from datetime import datetime, timedelta
from web3.exceptions import ABIFunctionNotFound, ContractLogicError
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ABI untuk router kontrak
ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "WETH",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ROUTER_ADDRESS = config.ROUTER_ADDRESS
MAX_UINT256 = 2**256 - 1

def setup_web3():
    w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    if not w3.is_connected():
        logger.error(f"Tidak dapat terhubung ke node: {config.RPC_URL}")
        raise Exception("Koneksi ke node gagal")
    logger.info(f"Terhubung ke node: {config.RPC_URL}")
    accounts = [w3.eth.account.from_key(pk) for pk in config.PRIVATE_KEYS]
    return w3, accounts

def get_token_balance(w3, token_address, account_address):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=config.SUDT_ABI)
    try:
        balance = token_contract.functions.balanceOf(account_address).call()
        return balance
    except Exception as e:
        logger.error(f"Error saat mengambil saldo token {token_address}: {str(e)}")
        return 0

def check_allowance(w3, token_address, owner_address, spender_address):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=config.SUDT_ABI)
    try:
        allowance = token_contract.functions.allowance(owner_address, spender_address).call()
        logger.info(f"Current allowance for {token_address}: {allowance}")
        return allowance
    except ABIFunctionNotFound:
        logger.warning(f"Allowance function not found for {token_address}. Assuming no allowance.")
        return 0

def get_dynamic_gas_price(w3, multiplier=1.1):
    gas_price = w3.eth.gas_price
    return int(gas_price * multiplier)

def approve_token(w3, account, token_address, spender_address):
    current_allowance = check_allowance(w3, token_address, account.address, spender_address)
    if current_allowance >= MAX_UINT256 // 2:
        logger.info(f"Allowance already sufficient for {token_address}")
        return True

    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=config.SUDT_ABI)

    try:
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        gas_price = get_dynamic_gas_price(w3)

        tx = token_contract.functions.approve(Web3.to_checksum_address(spender_address), MAX_UINT256).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            logger.info(f"Infinite approval successful for {token_address}")
            return True
        else:
            logger.error(f"Approval failed for {token_address}")
            return False
    except Exception as e:
        logger.warning(f"Error during approval for {token_address}: {str(e)}")
        return False

async def confirm_transaction(w3, tx_hash, max_attempts=60):
    for attempt in range(max_attempts):
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                if receipt['status'] == 1:
                    return True
                else:
                    logger.error(f"Transaksi gagal: {tx_hash.hex()}")
                    return False
        except Exception as e:
            logger.warning(f"Error saat memeriksa receipt (attempt {attempt + 1}/{max_attempts}): {str(e)}")
        await asyncio.sleep(2)  # Tunggu 2 detik sebelum mencoba lagi
    logger.error(f"Tidak ada konfirmasi untuk transaksi {tx_hash.hex()} setelah {max_attempts} percobaan")
    return False

async def check_router_contract(w3, router_address):
    try:
        logger.info(f"Memeriksa kontrak router di alamat: {router_address}")
        router_contract = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
        logger.info("Kontrak router berhasil dibuat")

        bytecode = w3.eth.get_code(router_address)
        if bytecode == b'':
            logger.error("Tidak ada bytecode di alamat kontrak yang diberikan")
            return False

        logger.info("Bytecode kontrak ditemukan")

        logger.info("Mencoba memanggil fungsi WETH()")
        try:
            weth_address = router_contract.functions.WETH().call()
            logger.info(f"Router contract verified. WETH address: {weth_address}")
        except ContractLogicError as cle:
            logger.error(f"Kesalahan logika kontrak: {str(cle)}")
            return False
        except ABIFunctionNotFound:
            logger.error("Fungsi WETH() tidak ditemukan dalam ABI kontrak")
            return False
        return True
    except Exception as e:
        logger.error(f"Error saat memeriksa kontrak router: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        return False

async def swap_token_with_retry(w3, account, token_address, amount, max_retries=5):
    router_contract = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)

    weth_address = router_contract.functions.WETH().call()
    path = [Web3.to_checksum_address(token_address), weth_address]
    deadline = int(time.time()) + 600  # 10 menit dari sekarang

    for attempt in range(max_retries):
        try:
            ckb_balance = w3.eth.get_balance(account.address)
            logger.info(f"Saldo CKB sebelum swap: {ckb_balance}")
            if ckb_balance < 1e16:  # 0.01 CKB
                logger.error(f"Saldo CKB tidak cukup untuk swap: {ckb_balance}")
                return False

            balance_before = get_token_balance(w3, token_address, account.address)
            ip_balance_before = w3.eth.get_balance(account.address)
            logger.info(f"Saldo sebelum swap - {token_address}: {balance_before}, IP (CKB): {ip_balance_before}")

            nonce = w3.eth.get_transaction_count(account.address, 'pending')
            gas_price = get_dynamic_gas_price(w3)

            # Penanganan khusus untuk WETH
            if token_address == config.TOKEN_ADDRESSES['WETH']:
                original_amount = amount
                for i in range(5):  # Coba hingga 5 kali dengan jumlah yang semakin kecil
                    amount = original_amount // (2**i)
                    amount_out_min = int(amount * 0.01)  # 99% slippage untuk WETH
                    logger.info(f"WETH swap attempt {i+1}: amount={amount}, amount_out_min={amount_out_min}")

                    try:
                        gas_estimate = router_contract.functions.swapExactTokensForETH(
                            amount, amount_out_min, path, account.address, deadline
                        ).estimate_gas({'from': account.address})
                        logger.info(f"Gas estimate successful for WETH: {gas_estimate}")
                        break
                    except ContractLogicError as e:
                        logger.warning(f"WETH swap attempt {i+1} failed. Error: {str(e)}")
                        if i == 4:  # Jika ini percobaan terakhir, raise error
                            raise
                        logger.warning("Trying with smaller amount.")
            else:
                amount_out_min = int(amount * 0.95)  # 5% slippage untuk token lain
                gas_estimate = router_contract.functions.swapExactTokensForETH(
                    amount, amount_out_min, path, account.address, deadline
                ).estimate_gas({'from': account.address})

            logger.info(f"Mencoba swap dengan parameter: amount={amount}, amount_out_min={amount_out_min}, path={path}, to={account.address}, deadline={deadline}")
            logger.info(f"Estimasi gas: {gas_estimate}")

            gas_limit = int(gas_estimate * 1.5)  # Tambahkan 50% ke estimasi gas

            tx = router_contract.functions.swapExactTokensForETH(
                amount,
                amount_out_min,
                path,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price
            })

            logger.info(f"Transaction built: {tx}")

            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Transaksi swap terkirim. Hash: {tx_hash.hex()}")
            logger.info(f"Silakan periksa transaksi di explorer: https://testnet.storyscan.xyz/tx/{tx_hash.hex()}")

            confirmation = await confirm_transaction(w3, tx_hash)
            if confirmation:
                balance_after = get_token_balance(w3, token_address, account.address)
                ip_balance_after = w3.eth.get_balance(account.address)
                logger.info(f"Swap berhasil. Saldo setelah swap - {token_address}: {balance_after}, IP (CKB): {ip_balance_after}")
                return True
            else:
                logger.error("Transaksi swap gagal dikonfirmasi")
                if attempt < max_retries - 1:
                    logger.info(f"Mencoba swap lagi... (Percobaan {attempt + 2}/{max_retries})")
                    await asyncio.sleep(5)
                else:
                    logger.error("Semua percobaan swap gagal.")
                    return False
        except Exception as e:
            logger.error(f"Error selama swap: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error args: {e.args}")
            if attempt < max_retries - 1:
                logger.info(f"Menunggu sebelum mencoba lagi... (Percobaan {attempt + 2}/{max_retries})")
                await asyncio.sleep(5)
            else:
                logger.error("Semua percobaan swap gagal.")
                return False

    return False

async def perform_swaps(w3, account):
    for token, address in config.TOKEN_ADDRESSES.items():
        balance = get_token_balance(w3, Web3.to_checksum_address(address), account.address)
        logger.info(f"Saldo saat ini dari {token}: {balance}")
        if balance > 0:
            current_allowance = check_allowance(w3, Web3.to_checksum_address(address), account.address, ROUTER_ADDRESS)
            if current_allowance < balance:
                if approve_token(w3, account, Web3.to_checksum_address(address), ROUTER_ADDRESS):
                    logger.info(f"Menunggu 15 detik setelah persetujuan untuk {token}")
                    await asyncio.sleep(15)  # Tunggu 15 detik setelah persetujuan
                else:
                    logger.error(f"Gagal melakukan approval untuk {token}")
                    continue

            ckb_balance = w3.eth.get_balance(account.address)
            logger.info(f"Saldo CKB: {ckb_balance}")

            if await swap_token_with_retry(w3, account, Web3.to_checksum_address(address), balance):
                logger.info(f"Berhasil menukar {balance} dari {token} ke IP untuk {account.address}")
            else:
                logger.error(f"Gagal menukar {token} untuk {account.address}")
        else:
            logger.info(f"Tidak ada saldo untuk {token} di {account.address}")

async def main():
    w3, accounts = setup_web3()

    logger.info(f"Menggunakan Router Address: {ROUTER_ADDRESS}")
    if not await check_router_contract(w3, ROUTER_ADDRESS):
        logger.error("Kontrak router tidak valid. Menghentikan program.")
        return

    try:
        while True:
            for account in accounts:
                logger.info(f"Performing swaps for {account.address}")
                await perform_swaps(w3, account)

            logger.info("All swaps completed. Waiting for 24 hours before next round.")
            next_run = datetime.now() + timedelta(hours=24)
            logger.info(f"Next run scheduled at: {next_run}")
            await asyncio.sleep(24 * 60 * 60)  # Sleep for 24 hours
    except KeyboardInterrupt:
        logger.info("Program dihentikan oleh pengguna.")
    except Exception as e:
        logger.error(f"Terjadi kesalahan yang tidak terduga: {str(e)}")
    finally:
        logger.info("Program selesai.")

if __name__ == "__main__":
    asyncio.run(main())