# `ChainSettle-SDK`

**ChainSettle-SDK** The ChainSettle SDK is a Python package designed to facilitate interactions with the ChainSettle API, enabling developers to manage off-chain settlement attestations and monitor their on-chain statuses seamlessly.

# Features

Initiate settlement attestations across various types (e.g., Plaid, PayPal).

Poll settlement status until reaching a terminal state.

Retrieve detailed settlement information.

Simulate signing processes for specific settlement types.

Manage validators and store salts associated with settlements.

# Installation
Ensure you have Python 3.7 or higher installed and either pip or uv package manager. Then, clone the repository:

```bash

git clone https://github.com/BrandynHamilton/chainsettle-sdk.git
cd chainsettle-
pip install uv # Only if not already installed
uv pip install -e .

```
# Usage
Here's a basic example of how to use the SDK:

```python

from chainsettle_sdk import ChainSettleService

# Initialize the service
chainsettle = ChainSettleService()

# Initiate a settlement attestation
response = chainsettle.initiate_attestation(
    settlement_id="unique_settlement_id",
    settlement_type="plaid",
    network="base",
    user_email="user@example.com",
    amount=10000,
    recipient_email="recipient@example.com",
    counterparty="0xCounterpartyAddress",
    metadata="Optional metadata"
)

print("Settlement initiated:", response)

```

For a more comprehensive example, refer to the main.py script included in the repository.

# Configuration
The SDK relies on a configuration module to manage settings such as API URLs and supported networks. Ensure that the chainsettle_sdk/config.py file is properly configured with the necessary parameters.

# Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your enhancements.

# License
This project is licensed under the MIT License. See the LICENSE file for details.