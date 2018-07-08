# Bitcoin SPV Client

Implementation of SPV protocol to verify Bitcoin transactions and check confirmations.

HingOn Miu


Steps:
- Run install.sh to install Python dependencies and Bitcoin core.

- Run Bitcoin full node to download complete raw .dat blockchain files.

- Run full_node_proxy.py as a central server to parse blockchain files.

- Run spv_client.py to download and parse block headers from full node proxy.

- Enter Bitcoin transaction ID to verify transactions and check confirmations.


Examples:
- Please enter a transaction ID to verify the Bitcoin transaction...
> 280a48a41cec0522214da1396511d7f3df669f13057c75519efac5cc8670eed9
  Confirmations: -1
  Transaction is not in main chain

- Please enter a transaction ID to verify the Bitcoin transaction...
> fe5be8db495cc8fe2da45f1b6da31d7033342805c8256438a3fdb60898cfb302
  Confirmations: 0
  Transaction is still reversible

- Please enter a transaction ID to verify the Bitcoin transaction...
> 19648c369b876714691db2e7f109b63ebfc9e8226e34328414f71a8b34d300fb
  Confirmations: 1
  Small amount transaction is likely secure

- Please enter a transaction ID to verify the Bitcoin transaction...
> b32ba68f44782a8dcd6d74cc4d9b44aa64cb773c2eeac5bf65203ab8ebd71e9e
  Confirmations: 11
  Large amount transaction is likely secure

- Please enter a transaction ID to verify the Bitcoin transaction...
> 05f6721201dba5703e2e1d1d0879e322861ca52fc922cde7fdbaff34930501d4
  Confirmations: 211
  Transaction is close to irreversible

- Please enter a transaction ID to verify the Bitcoin transaction...
> ee475443f1fbfff84ffba43ba092a70d291df233bd1428f3d09f7bd1a6054a1f
  Confirmations: -1
  Full node proxy could not find transaction

- Please enter a transaction ID to verify the Bitcoin transaction...
> fe5be8db495cc8fe2da45f1b6da                                     
  Transaction ID shoud be 64 characters.

- Please enter a transaction ID to verify the Bitcoin transaction...
> fe5be8db495cc8fe2da45f1b6da@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
  Transaction ID shoud be hexadecimal.



