# Decentralized Real Estate Ownership Management System

## Project Overview
This project is a decentralized web application designed to tokenize and manage real estate ownership using Blockchain technology. Instead of relying on traditional Ethereum Smart Contracts, the system integrates directly with the Bitcoin Core network (Regtest environment) and utilizes the Hierarchical Deterministic (HD) Wallet architecture (BIP-32/BIP-39 standards).
Physical assets (land use right certificates) are tokenized by anchoring the SHA-256 hash of their legal records to the blockchain via the `OP_RETURN` script, while simultaneously issuing an Unspent Transaction Output (UTXO) valued at exactly 0.001 BTC to act as the unique digital token representing the asset.

## Core Features

* **Role-Based Access Control:** Provides distinct interfaces and cryptographic authorizations for Sellers (Citizen A), Buyers (Citizen B), and the Land Registry Authority (System Admin).
* **Asset Registration:** Citizens input property metadata and upload images of physical land certificates to initiate a tokenization request.
* **Legal Verification & Token Minting:** The administrative authority audits the off-chain records and executes on-chain token minting (UTXO issuance) to certify legitimate properties.
* **UTXO-Based Ownership Transfer:** Owners use their private key (ECDSA) to digitally sign and transfer the asset directly to a buyer's wallet, effectively eliminating the risk of double-spending or fraudulent multi-party sales.
* **Transaction History Tracking:** All ownership changes are permanently recorded on Bitcoin Core and can be transparently audited by the public via the "Bitcoin Network Anchor Logs" interface.

## Tech Stack

* **Presentation Layer (Frontend):** HTML5, JavaScript, Tailwind CSS.
* **Business Logic Layer (Backend):** Python Flask (v3.x).
* **Blockchain Ledger:** Bitcoin Core (Regtest Node) communicating via the JSON-RPC protocol.
* **Cryptography & Wallet Management:** HD Wallet (mnemonic, bip_utils), SHA-256 hashing algorithm, Elliptic Curve Cryptography (secp256k1) digital signatures.
* **Off-chain Database:** SQL/NoSQL (or in-memory RAM for simulation) to securely store Personally Identifiable Information (PII) and heavy image files, ensuring compliance with Bitcoin's strict block size limits.

## System Architecture

The system is built on a 3-Tier Architecture to ensure high performance, security, and a strict separation of concerns:

1. **Presentation Layer (Frontend UI):** Collects user inputs and ECDSA digital signatures, communicating with the backend via standard HTTP POST requests without exposing complex blockchain logic to the user.
2. **Business Logic Layer (Python Middleware):** Acts as a "pseudo-smart contract" that manages HD Wallets, executes SHA-256 hashing, and strictly isolates end-users from direct access to the blockchain network.
3. **Ledger Layer (Bitcoin Core Node):** The decentralized ledger that executes JSON-RPC commands to verify signatures, transfer UTXOs, and finalize immutable blocks.

## Project Authors
**Team 15:**
* Nguyen Pham Quynh Trang - Leader
* Pham Huong Giang
* Hoang Bui Minh Ngoc
