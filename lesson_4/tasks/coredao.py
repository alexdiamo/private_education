import asyncio
import random
from typing import Optional
from web3.types import TxParams
from web3.contract import AsyncContract
from tasks.base import Base
from py_eth_async.data.models import TxArgs, TokenAmount, Networks, RawContract
from data.config import logger
from data.models import Contracts

class Coredao(Base):
    contracts = {
        'BSC_COREDAO': Contracts.BSC_COREDAO,
        'BSC_USDT': Contracts.BSC_USDT
    }

    async def swap(
            self,
            token_name: str,
            to_network_name: str,
            amount: Optional[TokenAmount] = None,
            slippage: float = 0.5,
            max_fee: float = 1
    ):
        token_name = token_name.upper()
        from_network_name = self.client.network.name
        to_network_name = to_network_name.lower()
        failed_text = f'Failed to send {from_network_name} {token_name} to {to_network_name} {token_name} via Coredao'

        if from_network_name == to_network_name:
            return f'{failed_text}: The same source and destination network'

        token_contract = await self.client.contracts.default_token(
            contract_address=Coredao.contracts[f'{from_network_name.upper()}_{token_name}'].address
        )
        coredao_contract = await self.client.contracts.get(
            contract_address=Coredao.contracts[f'{from_network_name.upper()}_COREDAO']
        )

        args = TxArgs(
            token=token_contract.address,
            amountLD=amount.Wei,
            to=self.client.account.address,
            callParams=TxArgs(
                refundAddress=self.client.account.address,
                zroPaymentAddress='0x0000000000000000000000000000000000000000'
            ).tuple(),
            adapterParams='0x'
        )
        print(args)

        value = await self.get_value(router_contract=coredao_contract)
        print(value)

        if not value:
            return f'{failed_text} | can not get value ({from_network_name})'

        native_balance = await self.client.wallet.balance()
        print(native_balance)

        if native_balance.Wei < value.Wei:
            return f'{failed_text}: To low native balance: balance: {native_balance.Ether}; value: {value.Ether}'

        token_price = await self.get_token_price(token=self.client.network.coin_symbol)
        network_fee = float(value.Ether) * token_price

        if network_fee > max_fee:
            return f'{failed_text} | too high fee: {network_fee} ({from_network_name})'

        if await self.approve_interface(
                token_address=token_contract.address,
                spender=coredao_contract.address,
                amount=amount
        ):
            await asyncio.sleep(random.randint(5, 10))
        else:
            return f'{failed_text} | can not approve'

        print('approved interface')

        tx_params = TxParams(
            to=coredao_contract.address,
            data=coredao_contract.encodeABI('bridge', args=args.tuple()),
            value=value.Wei
        )
        print(tx_params)

        tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

        if receipt:
            return f'{amount.Ether} {token_name} was send from {from_network_name} to {to_network_name} via Coredao: {tx.hash.hex()}'

        return f'{failed_text}!'


    async def get_value(self, router_contract: AsyncContract):
        res = await router_contract.functions.estimateBridgeFee(True, '0x').call()
        return TokenAmount(amount=res[0], wei=True)
