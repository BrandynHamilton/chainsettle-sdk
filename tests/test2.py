from itertools import chain
from chainsettle_sdk import ChainSettleService
from web3 import Web3
import json
import os

def main(settlement_type, network, counterparty,
            recipient_email, amount, settlement_id=None,  
            witness=None, metadata=None, user_email=None):
    
    BASE_DIR = os.path.dirname(__file__)
    ABI_PATH = os.path.join(BASE_DIR, 'abi', 'settlementRegistryAbi.json')
    
    GATEWAY = os.getenv("GATEWAY", None)
    if GATEWAY is None:
        raise ValueError("GATEWAY environment variable is not set. Please set it to your Alchemy or Infura endpoint.")
    
    chainsettle = ChainSettleService()

    config = chainsettle.get_config_map()

    CHAINSETTLE_SETTLEMENT_REGISTRY = config[network]['registry_addresses']['SettlementRegistry']
    
    # CHAINSETTLE_SETTLEMENT_REGISTRY = os.getenv("CHAINSETTLE_SETTLEMENT_REGISTRY", None)
    if CHAINSETTLE_SETTLEMENT_REGISTRY is None:
        raise ValueError("CHAINSETTLE_SETTLEMENT_REGISTRY environment variable is not set. Please set it to the settlement registry contract address.")
    
    if not os.path.exists(ABI_PATH):
        raise FileNotFoundError(f"ABI file not found at {ABI_PATH}. Please ensure the ABI file is present in the specified path.")
    
    abi = json.load(open(ABI_PATH, 'r'))
    
    w3 = Web3(Web3.HTTPProvider(GATEWAY))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to the Ethereum network. Please check your GATEWAY URL.")
    
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CHAINSETTLE_SETTLEMENT_REGISTRY),
        abi=abi
    )

    chainsettle = ChainSettleService(contract=contract)

    print("Supported Networks:", chainsettle.supported_networks)
    print("Supported APIs:", chainsettle.supported_apis)
    print("Supported Asset Categories:", chainsettle.supported_asset_categories)
    print("Supported Jurisdictions:", chainsettle.supported_jurisdictions)

    resp = chainsettle.get_validator_list()
    print("Validator List:", json.dumps(resp, indent=2))

    print("Initiating settlement...")
    resp = chainsettle.initiate_attestation(
        settlement_id=settlement_id,
        network=network,
        settlement_type=settlement_type,
        amount=amount,
        recipient_email=recipient_email,
        counterparty = counterparty,
        witness=witness,
        details=metadata,
        user_email=user_email
    )

    print("Settlement initiated successfully.")
    print(json.dumps(resp, indent=2))

    if settlement_type == 'plaid':

        chainsettle.poll_settlement_status_onchain(statuses=[1], finalized_flag=False) # check if registered

        resp = chainsettle.attest_settlement()

        print("Settlement attested successfully.")

        print(f'resp',resp)

    resp = chainsettle.poll_settlement_status_onchain()

    if resp:
        print("Settlement activity polled successfully.")
        print(json.dumps(resp, indent=2))

    return "Settlement registered and activity polled successfully."

if __name__ == "__main__":
    import secrets
    settlement_type = "paypal"
    network = "base"
    counterparty = "0x38979DFdB5d8FD76FAD4E797c4660e20015C6a84"
    recipient_email = "treasuryops@defiprotocol.com"
    amount = 1000
    user_email = "brandynham1120@gmail.com"
    witness = "0x6f8550D4B3Af628d5eDe06131FE60A1d2A5DE2Ab"
    metadata = "Test settlement for ChainSettle SDK"

    print("Running ChainSettle SDK Test")

    main(
        settlement_type=settlement_type,
        network=network,
        counterparty=counterparty,
        witness=witness,
        recipient_email=recipient_email,
        amount=amount,
        user_email=user_email,
        metadata=metadata,
    )