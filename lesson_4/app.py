import asyncio
from loguru import logger
from py_eth_async.data.models import Networks, TokenAmount, TxArgs
from py_eth_async.client import Client
from data.models import Contracts
from private_data import private_key1
from tasks.base import Base
from tasks.woofi import WooFi
from tasks.stargate import Stargate
from tasks.coredao import Coredao
from tasks.uniswap import Uniswap

async def main():
    # client = Client(private_key=private_key1, network=Networks.Avalanche)
    # stargate = Stargate(client=client)

    # status = await stargate.send_usdc(
    #     to_network_name=Networks.Polygon.name,
    #     amount=TokenAmount(0.5, decimals=6)
    # )

    # status = await stargate.send_usdc_from_avalanche_to_usdt_bsc(
    #     amount=TokenAmount(0.5, decimals=6),
    #     dest_fee=TokenAmount(0.005),
    #     max_fee=1.1
    # )
    # $5.55
    # $0.74

    # 3.27
    # 1.89

    # if 'Failed' in status:
    #     logger.error(status)
    # else:
    #     logger.success(status)

    # res = await client.transactions.decode_input_data(
    #     client=client,
    #     contract=Contracts.AVALANCHE_USDC,
    #     input_data='0x9fbf10fc000000000000000000000000000000000000000000000000000000000000006600000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000002b8491765536b7d4fe3e59db46596e1f577ecb000000000000000000000000000000000000000000000000000000000007a120000000000000000000000000000000000000000000000000000000000007975c000000000000000000000000000000000000000000000000000000000000012000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002386f26fc1000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000014002b8491765536b7d4fe3e59db46596e1f577ecb0000000000000000000000000000000000000000000000000000000000000000000000000000000000000014002b8491765536b7d4fe3e59db46596e1f577ecb0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    # )
    # for key, val in res[1].items():
    #     if isinstance(val, bytes):
    #         print(key, val.hex())
    #     elif isinstance(val, tuple):
    #         print(key, '(', end=' ')
    #         for item in val:
    #             if isinstance(item, bytes):
    #                 print(item.hex(), end=', ')
    #             else:
    #                 print(item, end=', ')
    #         print(')')
    #     else:
    #         print(key, val)

    pass

    # task 1
    # client = Client(private_key=private_key1, network=Networks.Optimism)
    # stargate = Stargate(client=client)
    # res = await stargate.send_usdc(
    #     to_network_name='polygon',
    #     max_fee=0.5
    # )
    # print(res)

    # task 2
    # network = await Stargate.get_network_with_usdc(address='')
    # print(network)

    # task 3
    # client = Client(private_key=private_key1, network=Networks.BSC)
    # coredao = Coredao(client=client)
    # res = await coredao.swap(
    #     to_network_name='coredao',
    #     token_name='USDT',
    #     amount=TokenAmount(amount=0.6, decimals=18),
    #     max_fee=0.5
    # )
    # print(res)

    # task 4
    # client = Client(private_key=private_key1, network=Networks.Arbitrum)
    # uniswap = Uniswap(client=client)
    # res = await uniswap.swap_arb_eth_to_geth(amount_geth=TokenAmount(amount=0.0005))
    # print(res)


async def find_token_with_higher_balance(private_key: str, token_name: str):
    token_name = token_name.upper()

    contracts = vars(Contracts)
    networks = [
        Networks.Arbitrum,
        Networks.Polygon,
        Networks.Avalanche,
        Networks.Optimism
    ]

    balance = 0
    client = None

    for network in networks:
        contract_key = f'{network.name.upper()}_{token_name}'

        if contract_key not in contracts:
            continue

        client = Client(private_key=private_key, network=network)

        if network.coin_symbol == token_name:
            _balance = await client.wallet.balance()
        else:
            contract = contracts[contract_key]
            _balance = await client.wallet.balance(token=contract.address)

        print(f'Found {_balance.Ether} {token_name} in network {client.network.name}')

        if _balance > balance:
            balance = _balance

    if balance:
        print(f'SUCCESS | Higher balance: {balance.Ether} {token_name} in network {client.network.name}')

    return balance

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
