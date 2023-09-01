import asyncio
import random
import requests
import time
import json
from typing import Optional
from web3.types import TxParams
from web3.contract import AsyncContract
from tasks.base import Base
from py_eth_async.data.models import TxArgs, TokenAmount, Networks, RawContract
from data.config import logger
from data.models import Contracts
from fake_useragent import UserAgent

class Uniswap(Base):

    async def swap_arb_eth_to_geth(
            self,
            amount_geth: TokenAmount,
            slippage: float = 1
    ):
        amount_eth = await self.get_price(amount=amount_geth, slippage=slippage)
        print(amount_eth)

        uniswap_contract = await self.client.contracts.get(contract_address=Contracts.ARBITRUM_UNISWAP)

        input1 = '0x' + ''.join([
            '2'.zfill(64),
            hex(amount_eth.Wei)[2:].zfill(64)
        ])
        input2 = '0x' + ''.join([
            '1'.zfill(64),
            hex(amount_geth.Wei)[2:].zfill(64),
            hex(amount_eth.Wei)[2:].zfill(64),
            'a0'.zfill(64),
            '0'.zfill(64),
            '2b'.zfill(64),
            'dd69db25f6d620a7bad3023c5d32761d353d3de90001f482af49447d8a07e3bd',
            '95bd0d56f35241523fbab1000000000000000000000000000000000000000000'
        ])
        input3 = '0x' + ''.join([
            '1'.zfill(64),
            '0'.zfill(64)
        ])

        args = TxArgs(
            commands='0x0b010c',
            inputs=[input1, input2, input3],
            deadline=int(time.time()) + 30 * 60
        )
        print(args)

        tx_params = TxParams(
            to=uniswap_contract.address,
            data=uniswap_contract.encodeABI('execute', args=args.tuple()),
            value=amount_eth.Wei
        )

        tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

        if receipt:
            return f'{amount_eth.Ether} ETH was swapped to {amount_geth.Ether} in Arbitrum via Uniswap: {tx.hash.hex()}'

        return f'Failed to swap ETH to GETH in Arbitrum via Uniswap!'

    async def get_price(self, amount: TokenAmount, slippage: float = 1) -> TokenAmount:
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://app.uniswap.org/',
            'user-agent': UserAgent().chrome,
        }

        data = {
            'tokenInChainId': 42161,
            'tokenIn': 'ETH',
            'tokenOutChainId': 42161,
            'tokenOut': str(Contracts.ARBITRUM_GETH.address),
            'amount': str(amount.Wei),
            'type': 'EXACT_OUTPUT',
            'configs': [{
                'protocols': ['V2', 'V3', 'MIXED'],
                'routingType': 'CLASSIC'
            }]
        }
        print(data)

        res = requests.post('https://api.uniswap.org/v2/quote', headers=headers, data=json.dumps(data))
        data = res.json()
        print(data)

        quote = int(data['quote']['quote'])
        slippage = slippage * -1
        amount_with_slippage = int(quote * (100 - slippage) / 100)
        return TokenAmount(amount=amount_with_slippage, decimals=18, wei=True)
