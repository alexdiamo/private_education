import asyncio
from typing import Optional
from web3.types import TxParams
from py_eth_async.data.models import TxArgs, TokenAmount

from data.models import Contracts
from tasks.base import Base

class WooFi(Base):

    def get_contract(self, name: str):
        name = name.upper()
        if name == 'ARBITRUM_WOOFI':
            return Contracts.ARBITRUM_WOOFI
        elif name == 'ARBITRUM_ETH':
            return Contracts.ARBITRUM_ETH
        elif name == 'ARBITRUM_USDC':
            return Contracts.ARBITRUM_USDC
        elif name == 'ARBITRUM_USDT':
            return Contracts.ARBITRUM_USDT
        elif name == 'ARBITRUM_WBTC':
            return Contracts.ARBITRUM_WBTC

    # swap from any token to any token in arbitrum
    async def swap_arbitrum(
            self,
            from_token: str,
            to_token: str,
            amount: Optional[TokenAmount] = None,
            slippage: float = 1
    ):
        native_token = 'ETH'
        from_token = from_token.upper()
        to_token = to_token.upper()

        contract = await self.client.contracts.get(contract_address=Contracts.ARBITRUM_WOOFI)
        from_token_contract = self.get_contract(name=f'ARBITRUM_{from_token}')
        to_token_contract = self.get_contract(name=f'ARBITRUM_{to_token}')

        if not from_token_contract:
            return f'Contract {from_token} not found'

        if not to_token_contract:
            return f'Contract {to_token} not found'

        if from_token != native_token:
            if not amount:
                amount = await self.client.wallet.balance(token=from_token_contract)

            await self.approve_interface(
                token_address=from_token_contract.address,
                spender=contract.address,
                amount=amount
            )
            await asyncio.sleep(5)

        price = await self.get_price(token=from_token, in_token=to_token)
        multiplier = (1 - slippage / 100)

        if to_token == native_token:
            min_to_amount = TokenAmount(
                amount=price * float(amount.Ether) * multiplier
            )
        else:
            min_to_amount = TokenAmount(
                amount=price * float(amount.Ether) * multiplier,
                decimals=await self.get_decimals(contract_address=to_token_contract.address)
            )

        args = TxArgs(
            fromToken=from_token_contract.address,
            toToken=to_token_contract.address,
            fromAmount=amount.Wei,
            minToAmount=min_to_amount.Wei,
            to=self.client.account.address,
            rebateTo=self.client.account.address,
        )

        if from_token != native_token:
            tx_params = TxParams(
                to=contract.address,
                data=contract.encodeABI('swap', args=args.tuple())
            )
        else:
            tx_params = TxParams(
                to=contract.address,
                data=contract.encodeABI('swap', args=args.tuple()),
                value=amount.Wei
            )

        tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=200)

        if receipt:
            return f'{amount.Ether} {from_token} was swapped to {min_to_amount.Ether} {to_token} via WooFi: {tx.hash.hex()}'

        return f'Failed swap {from_token} to {to_token} via WooFi!'

    async def swap_eth_to_usdc(self, amount: TokenAmount, slippage: float = 1):
        failed_text = 'Failed swap ETH to USDC via WooFi'

        contract = await self.client.contracts.get(contract_address=Contracts.ARBITRUM_WOOFI)
        from_token = Contracts.ARBITRUM_ETH
        to_token = Contracts.ARBITRUM_USDC

        eth_price = await self.get_token_price(token='ETH')
        min_to_amount = TokenAmount(
            amount=eth_price * float(amount.Ether) * (1 - slippage / 100),
            decimals=await self.get_decimals(contract_address=to_token.address)
        )

        args = TxArgs(
            fromToken=from_token.address,
            toToken=to_token.address,
            fromAmount=amount.Wei,
            minToAmount=min_to_amount.Wei,
            to=self.client.account.address,
            rebateTo=self.client.account.address,
        )

        tx_params = TxParams(
            to=contract.address,
            data=contract.encodeABI('swap', args=args.tuple()),
            value=amount.Wei
        )

        tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=200)

        if receipt:
            return f'{amount.Ether} ETH was swapped to {min_to_amount.Ether} USDC via WooFi: {tx.hash.hex()}'

        return f'{failed_text}!'

    async def swap_usdc_to_eth(self, amount: Optional[TokenAmount] = None, slippage: float = 1):
        failed_text = 'Failed swap USDC to ETH via WooFi'

        contract = await self.client.contracts.get(contract_address=Contracts.ARBITRUM_WOOFI)
        from_token = Contracts.ARBITRUM_USDC
        to_token = Contracts.ARBITRUM_ETH

        if not amount:
            amount = await self.client.wallet.balance(token=from_token)

        await self.approve_interface(token_address=from_token.address, spender=contract.address, amount=amount)
        await asyncio.sleep(5)

        eth_price = await self.get_token_price(token='ETH')
        min_to_amount = TokenAmount(
            amount=float(amount.Ether) / eth_price * (1 - slippage / 100)
        )

        args = TxArgs(
            fromToken=from_token.address,
            toToken=to_token.address,
            fromAmount=amount.Wei,
            minToAmount=min_to_amount.Wei,
            to=self.client.account.address,
            rebateTo=self.client.account.address,
        )

        tx_params = TxParams(
            to=contract.address,
            data=contract.encodeABI('swap', args=args.tuple())
        )

        tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=200)

        if receipt:
            return f'{amount.Ether} USDC was swapped to {min_to_amount.Ether} ETH via WooFi: {tx.hash.hex()}'

        return f'{failed_text}!'
