
# Konfigurasi Web3
RPC_URL = "https://testnet.storyrpc.io"

# Daftar private key
PRIVATE_KEYS = [
]

# Alamat kontrak token (fokus pada SUDT)
TOKEN_ADDRESSES = {
    "SUSDT": "0x8812d810EA7CC4e1c3FB45cef19D6a7ECBf2D85D",
    "SUSDC": "0x700722D24f9256Be288f56449E8AB1D27C4a70ca",
    "WBTC": "0x153B112138C6dE2CAD16D66B4B6448B7b88CAEF3",
    "WETH": "0x968B9a5603ddEb2A78Aa08182BC44Ece1D9E5bf0"
}

# ABI untuk kontrak ERC20 (ini adalah ABI minimal, mungkin perlu disesuaikan)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# ABI untuk kontrak SUDT (sesuaikan dengan ABI yang terlihat di halaman kontrak)
SUDT_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [],
        "name": "claim",
        "outputs": [],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "lastClaimTime",
        "outputs": [{"name": "timestamp", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
    # ... tambahkan fungsi lain yang mungkin diperlukan
]

# Hapus atau komentari baris di bawah ini
# c8c4becc7a39958c839f680fa583289ede7c43342fde12096fe8024b3682c25a

# Alamat factory (jika ada)
# FACTORY_ADDRESS = "0x..."  # Isi dengan alamat factory yang benar

# Alamat router (sebagai fallback jika tidak bisa mendapatkan dari factory)
ROUTER_ADDRESS = "0x56300f2dB653393e78C7b5edE9c8f74237B76F47"  # Isi dengan alamat router yang benar dari transaksi manual


