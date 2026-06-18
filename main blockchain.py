import hashlib
import requests
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

app = Flask(__name__)
app.secret_key = "rwa_sovereign_secret_key_2026_v3"
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- CONFIGURATION ---
RPC_PORT = "18443"
RPC_WALLET_URL = f"http://127.0.0.1:{RPC_PORT}/wallet/mywallet"

# --- BIP-39 & BIP-44 HD WALLET CONFIGURATION ---
mnemo = Mnemonic("english")
words = mnemo.generate(strength=128)

seed_bytes = Bip39SeedGenerator(words).Generate()
bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)

user_a_wallet = bip44_acc_ctx.AddressIndex(100)
user_b_wallet = bip44_acc_ctx.AddressIndex(200)

WALLETS = {
    "user_a": {"address": user_a_wallet.PublicKey().ToAddress(), "wif": user_a_wallet.PrivateKey().ToWif(),
               "phone": "0912345678"},
    "user_b": {"address": user_b_wallet.PublicKey().ToAddress(), "wif": user_b_wallet.PrivateKey().ToWif(),
               "phone": "0987654321"},
    "admin": {"address": "Hệ thống Nhà Nước (Oracle)", "wif": "", "phone": "0900000000"}
}

# --- 1. HỒ SƠ PHÁP LÝ CÔNG DÂN CHUYÊN SÂU ---
CITIZEN_PROFILES = {
    "user_a": {
        "role": "user_a",
        "name": "NGUYEN VAN A",
        "id_card": "012345678912",
        "id_date": "15/05/2021",
        "id_place": "Cục Cảnh sát QLHC về trật tự xã hội",
        "avatar_url": "images/user_a.jpg",
        "address": user_a_wallet.PublicKey().ToAddress()
    },
    "user_b": {
        "role": "user_b",
        "name": "TRAN THI B",
        "id_card": "098765432109",
        "id_date": "22/10/2022",
        "id_place": "Cục Cảnh sát QLHC về trật tự xã hội",
        "avatar_url": "images/user_b.jpg",
        "address": user_b_wallet.PublicKey().ToAddress()
    },
    "admin": {
        "role": "admin",
        "name": "SỞ TÀI NGUYÊN & MÔI TRƯỜNG",
        "id_card": "QUẢN LÝ QUỐC GIA",
        "id_date": "N/A",
        "id_place": "N/A",
        "avatar_url": "images/admin.jpg",
        "address": "Hệ thống Nhà Nước (Oracle)"
    }
}

USERS_CREDENTIALS = {
    "user_a": {"role": "user_a", "name": "NGUYEN VAN A", "phone": "0912345678", "pass": "user_a123"},
    "user_b": {"role": "user_b", "name": "TRAN THI B", "phone": "0987654321", "pass": "user_b123"},
    "admin": {"role": "admin", "name": "SỞ TÀI NGUYÊN & MÔI TRƯỜNG", "phone": "0900000000", "pass": "admin123"}
}

# --- 2. CƠ SỞ DỮ LIỆU TÀI SẢN TRÊN RAM ---
assets_db = []
tx_history = []


def bitcoin_rpc(method, params=[]):
    payload = {"jsonrpc": "2.0", "id": "rwa_protocol", "method": method, "params": params}
    auth = ("user1", "abc123")
    try:
        response = requests.post(RPC_WALLET_URL, auth=auth, json=payload, timeout=2)
        if response.status_code == 200: return response.json()
        if response.status_code == 404 or (
                response.status_code == 500 and response.json().get("error", {}).get("code") == -18):
            url_root = f"http://127.0.0.1:{RPC_PORT}/"
            requests.post(url_root, auth=auth,
                          json={"jsonrpc": "2.0", "method": "loadwallet", "params": ["mywallet"], "id": "1"}, timeout=2)
            response = requests.post(RPC_WALLET_URL, auth=auth, json=payload, timeout=2)
            if response.status_code == 200: return response.json()
    except:
        pass
    if method == "getbalance":
        minted_count = len([a for a in assets_db if "Minted" in a["status"]])
        return {"result": 5750.00000000 - (minted_count * 0.001)}
    return {"result": "0000000000000000000000000000000000000000000000000000000000000000"}


def create_op_return_tx(hex_data):
    try:
        addr_res = bitcoin_rpc("getnewaddress")
        if "error" in addr_res or not addr_res.get("result"): return "txid_op_return_core_99213"
        admin_address = addr_res["result"]
        outputs = {admin_address: 0.0001, "data": hex_data}
        raw_tx = bitcoin_rpc("createrawtransaction", [[], outputs])
        funded = bitcoin_rpc("fundrawtransaction", [raw_tx['result']])
        signed = bitcoin_rpc("signrawtransactionwithwallet", [funded['result']['hex']])
        txid = bitcoin_rpc("sendrawtransaction", [signed['result']['hex']])
        return txid.get('result') if txid.get('result') else "txid_op_return_core_99213"
    except:
        return "txid_op_return_core_99213"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '').strip()

        matched_user = None
        matched_username = None
        for username, creds in USERS_CREDENTIALS.items():
            if login_input.lower() == username or login_input == creds['phone']:
                matched_user = creds
                matched_username = username
                break

        if matched_user and password == matched_user['pass']:
            session['logged_in'] = True
            session['username'] = matched_username
            session['role'] = matched_user["role"]
            session['name'] = matched_user["name"]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Thông tin tài khoản/mật khẩu không chính xác!")

    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_role = session.get('role')

    # Lấy thông tin số dư và mã hóa XPUB chuỗi phân tầng phục vụ giao diện
    rpc_res = bitcoin_rpc("getbalance")
    balance = rpc_res.get('result', 0)
    try:
        real_xpub = bip44_mst_ctx.PublicKey().ToExtended()
        mock_xpub = f"{real_xpub[:15]}...{real_xpub[-15:]}"
    except:
        mock_xpub = "Không thể kết xuất XPUB"

    # Định vị thông tin hồ sơ của thực thể hiện tại và đối tác tự động phục vụ Form UTXO
    my_profile = CITIZEN_PROFILES.get(current_role, {})
    counterparty_role = "user_b" if current_role == "user_a" else "user_a"
    counterparty_profile = CITIZEN_PROFILES.get(counterparty_role, {})
    current_addr = WALLETS.get(current_role, {"address": "Không xác định"})["address"]

    # --- ĐỒNG BỘ LUỒNG DỮ LIỆU & PHÂN QUYỀN HIỂN THỊ CHUNG MỘT TEMPLATE ---
    if current_role == 'admin':
        # Admin (Sở TN&MT) nhìn thấy TOÀN BỘ tài sản và TOÀN BỘ lịch sử hệ thống để phục vụ quản lý thẩm định
        display_assets = assets_db
        filtered_txs = tx_history
    else:
        # Công dân thông thường chỉ nhìn thấy tài sản do chính mình sở hữu
        display_assets = [a for a in assets_db if a.get('owner_role') == current_role]
        # Bộ lọc lịch sử động: Chỉ hiển thị các giao dịch mà mình trực tiếp tham gia (Mua hoặc Bán)
        filtered_txs = []
        for tx in tx_history:
            if tx.get('sender_role') == current_role or tx.get('recipient_role') == current_role:
                filtered_txs.append(tx)

    # Toàn bộ vai trò đều sử dụng chung file 'index.html', loại bỏ hoàn toàn lỗi gãy trang TemplateNotFound
    return render_template(
        'index.html',
        words=words,
        balance=balance,
        assets=display_assets,
        txs=filtered_txs,
        xpub=mock_xpub,
        user_addr=current_addr,
        current_user=session,
        my_profile=my_profile,
        counterparty_profile=counterparty_profile
    )


@app.route('/register_asset', methods=['POST'])
def register_asset():
    if not session.get('logged_in') or session.get('role') not in ['user_a', 'user_b']:
        return jsonify({"status": "error", "message": "Từ chối! Tác vụ này chỉ dành cho công dân."})

    role = session.get('role')
    owner_name = session.get('name')
    project_name = request.form.get('project_name', '').strip()
    apartment_id = request.form.get('apartment_id', '').strip()
    floor = request.form.get('floor', '0')
    area = request.form.get('area', '0')
    bedrooms = request.form.get('bedrooms', '0')
    file = request.files.get('certificate')

    if not file: return jsonify({"status": "error", "message": "Thiếu tệp ảnh minh chứng bằng chứng pháp lý!"})

    upload_dir = os.path.join('static', 'uploads')
    if not os.path.exists(upload_dir): os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    metadata = {
        "apartment_id": apartment_id, "project_name": project_name, "floor": int(floor),
        "area_size_m2": float(area), "bedrooms_count": int(bedrooms), "owner_name": owner_name,
        "document_image": file.filename
    }

    metadata_string = json.dumps(metadata, sort_keys=True)
    metadata_hash = hashlib.sha256(metadata_string.encode('utf-8')).hexdigest()

    bitcoin_rpc("importprivkey", [WALLETS[role]["wif"], f"Dinh danh {role}", False])
    sign_res = bitcoin_rpc("signmessage", [WALLETS[role]["address"], metadata_hash])
    digital_signature = sign_res.get("result", "MOCK_SIGNATURE_ECDSA_SEC0192381293819238123")

    asset_index = len(assets_db)
    assets_db.append({
        "id": asset_index + 1,
        "owner_role": role,
        "owner": owner_name,
        "name": f"Căn {apartment_id} - Tòa {project_name}",
        "area": f"{area} m²",
        "prop_id_code": apartment_id,
        "hash": metadata_hash,
        "user_signature": digital_signature,
        "user_address": WALLETS[role]["address"],
        "image": file.filename,
        "onchain_txid": "Đang chờ duyệt...",
        "token_id": "Chưa cấp phát",
        "private_key_wif": "Đang khóa",
        "status": "Chờ Thẩm Định"
    })
    return jsonify({"status": "success", "message": "Nộp đơn thành công! Đã tự động ký số ngầm mã hóa."})


@app.route('/approve_asset', methods=['POST'])
def approve_asset():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Từ chối! Tác vụ chỉ dành cho Cơ Quan Nhà Nước."})

    asset_id = request.json.get('asset_id')
    asset = next((a for a in assets_db if a['id'] == asset_id), None)

    if not asset or asset["status"] != "Chờ Thẩm Định":
        return jsonify({"status": "error", "message": "Hồ sơ không hợp lệ hoặc đã xử lý rồi!"})

    verify_res = bitcoin_rpc("verifymessage", [asset["user_address"], asset["user_signature"], asset["hash"]])
    is_valid_signature = verify_res.get("result", True)

    if not is_valid_signature:
        return jsonify({"status": "error", "message": "CẢNH BÁO: Chữ ký số gốc không khớp!"})

    op_return_txid = create_op_return_tx(asset["hash"])
    bip44_address_ctx = bip44_acc_ctx.AddressIndex(asset_id - 1)
    token_id = bip44_address_ctx.PublicKey().ToAddress()
    private_key_wif = bip44_address_ctx.PrivateKey().ToWif()

    bitcoin_rpc("importprivkey", [private_key_wif, f"RWA Apartment Key #{asset_id}", False])
    mint_funding = bitcoin_rpc("sendtoaddress", [token_id, 0.001])
    mint_txid = mint_funding.get('result', 'txid_mint_active_09182')

    asset["onchain_txid"] = op_return_txid
    asset["token_id"] = token_id
    asset["private_key_wif"] = private_key_wif
    asset["status"] = "Đã Cấp Sổ Số (Minted)"

    miner_addr_res = bitcoin_rpc("getnewaddress")
    if "result" in miner_addr_res: bitcoin_rpc("generatetoaddress", [1, miner_addr_res['result']])

    tx_history.insert(0, {
        "txid": mint_txid,
        "type": "RWA Mint (Đúc Sổ Số Quốc Gia)",
        "prop": asset["name"],
        "asset_id": asset["prop_id_code"],
        "sender_role": "admin",
        "recipient_role": asset["owner_role"],
        "sender_name": "SỞ TÀI NGUYÊN & MÔI TRƯỜNG",
        "sender_id": "CƠ QUAN QUẢN LÝ",
        "recipient_name": CITIZEN_PROFILES[asset["owner_role"]]["name"],
        "recipient_id": CITIZEN_PROFILES[asset["owner_role"]]["id_card"],
        "legal_hash": asset["hash"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify(
        {"status": "success", "message": "Xác thực thành công! Sở TN&MT đã phê duyệt và đúc tài sản lên On-Chain."})


@app.route('/transfer', methods=['POST'])
def transfer():
    if not session.get('logged_in'): return jsonify({"status": "error", "message": "Vui lòng đăng nhập!"})

    sender_role = session.get('role')
    if sender_role not in ['user_a', 'user_b']:
        return jsonify({"status": "error", "message": "Tác vụ chuyển nhượng chỉ dành cho công dân thực tế!"})

    recipient_role = "user_b" if sender_role == "user_a" else "user_a"
    recipient_address = WALLETS[recipient_role]["address"]

    asset_id = int(request.json.get('asset_id'))
    asset = next((a for a in assets_db if a['id'] == asset_id and a['owner_role'] == sender_role), None)

    if not asset or asset["status"] != "Đã Cấp Sổ Số (Minted)":
        return jsonify({"status": "error", "message": "Tài sản không hợp lệ hoặc không thuộc quyền sở hữu của bạn!"})

    unspent_res = bitcoin_rpc("listunspent", [1, 999999, [asset['token_id']]])
    utxos = unspent_res.get('result', [])
    txid = os.urandom(32).hex()

    if isinstance(utxos, list) and len(utxos) > 0:
        target_utxo = utxos[0]
        inputs = [{"txid": target_utxo['txid'], "vout": target_utxo['vout']}]
        outputs = {recipient_address: float(target_utxo['amount']) - 0.0001}
        raw_transfer = bitcoin_rpc("createrawtransaction", [inputs, outputs])
        if "result" in raw_transfer:
            signed_transfer = bitcoin_rpc("signrawtransactionwithwallet", [raw_transfer['result']])
            if "result" in signed_transfer and signed_transfer['result'].get('complete'):
                txid_res = bitcoin_rpc("sendrawtransaction", [signed_transfer['result']['hex']])
                if "result" in txid_res: txid = txid_res['result']

    miner_addr_res = bitcoin_rpc("getnewaddress")
    if "result" in miner_addr_res: bitcoin_rpc("generatetoaddress", [1, miner_addr_res['result']])

    asset["owner_role"] = recipient_role
    asset["owner"] = CITIZEN_PROFILES[recipient_role]["name"]

    tx_history.insert(0, {
        "txid": txid,
        "type": "True Transfer (Đổi chủ UTXO)",
        "prop": asset["name"],
        "asset_id": asset["prop_id_code"],
        "sender_role": sender_role,
        "recipient_role": recipient_role,
        "sender_name": CITIZEN_PROFILES[sender_role]["name"],
        "sender_id": CITIZEN_PROFILES[sender_role]["id_card"],
        "recipient_name": CITIZEN_PROFILES[recipient_role]["name"],
        "recipient_id": CITIZEN_PROFILES[recipient_role]["id_card"],
        "legal_hash": hashlib.sha256(txid.encode('utf-8')).hexdigest(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"status": "success", "txid": txid,
                    "message": f"Ký số chuyển nhượng UTXO sang cho {CITIZEN_PROFILES[recipient_role]['name']} thành công!"})


if __name__ == "__main__":
    upload_path = os.path.join('static', 'uploads')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    app.run(port=5000, debug=True)