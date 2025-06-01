from chainsettle_sdk import ChainSettleService
import json

def main(settlement_id, settlement_type, network, counterparty,
            recipient_email, amount, metadata=None, user_email=None):

    chainsettle = ChainSettleService()
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
        details=metadata,
        user_email=user_email
    )

    print("Settlement initiated successfully.")
    print(json.dumps(resp, indent=2))

    if settlement_type == 'plaid':

        chainsettle.poll_settlement_activity(settlement_id=settlement_id, statuses=[1]) # check if registered

        resp = chainsettle.attest_settlement(
            settlement_id=settlement_id
        )

        print("Settlement attested successfully.")

        print(f'resp',resp)

    resp = chainsettle.poll_settlement_activity(settlement_id=settlement_id)

    if resp:
        print("Settlement activity polled successfully.")
        print(json.dumps(resp, indent=2))

    return "Settlement registered and activity polled successfully."

if __name__ == "__main__":
    import secrets
    settlement_id = secrets.token_hex(4)
    settlement_type = "paypal"
    network = "base"
    payer = "0x38979DFdB5d8FD76FAD4E797c4660e20015C6a84"
    recipient_email = "onramp@settlement-ramp.com"
    amount = 10000
    user_email = "brandynham1120@gmail.com"
    counterparty = ""
    witness = ""
    metadata = "Test settlement for ChainSettle SDK"

    print("Running ChainSettle SDK Test")

    main(
        settlement_id=settlement_id,
        settlement_type=settlement_type,
        network=network,
        counterparty=counterparty,
        recipient_email=recipient_email,
        amount=amount,
        user_email=user_email,
        metadata=metadata,
    )