from web3 import Web3
from typing import Dict, Optional
import os
import json

class UniswapClient:
    """Cliente para interactuar con Uniswap v4"""
    
    def __init__(self, rpc_url: str = None, chain_id: int = 1):
        """
        Inicializa el cliente de Uniswap
        
        Args:
            rpc_url: URL del nodo RPC
            chain_id: ID de la cadena (1=Mainnet, 11155111=Sepolia, etc.)
        """
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://localhost:8545")
        self.chain_id = chain_id
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Verificar conexión
        if not self.w3.is_connected():
            print(f"Warning: No se puede conectar a {self.rpc_url}")
        
        # Direcciones de contratos (placeholder - actualizar con direcciones reales)
        self.pool_manager_address = os.getenv("POOL_MANAGER_ADDRESS", "")
        self.hook_address = os.getenv("HOOK_ADDRESS", "")
        self.invisible_transfer_address = os.getenv("INVISIBLE_TRANSFER_ADDRESS", "")
    
    def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        decimals_in: int = 18
    ) -> Dict:
        """
        Obtiene una cotización de Uniswap v4
        
        Args:
            token_in: Dirección del token de entrada
            token_out: Dirección del token de salida
            amount_in: Cantidad de tokens de entrada
            decimals_in: Decimales del token de entrada
            
        Returns:
            Dict con información de la cotización
        """
        # En una implementación real, se llamaría al PoolManager de Uniswap v4
        # Por ahora, devolvemos datos simulados
        
        amount_in_wei = int(amount_in * (10 ** decimals_in))
        
        # Simulación de cotización (en producción, llamar al contrato real)
        estimated_out = amount_in_wei * 0.98  # Simulación con 2% de slippage
        
        return {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in_wei,
            "amount_out_estimated": int(estimated_out),
            "price_impact": 2.0,
            "gas_estimated": 150000,
            "route": [token_in, token_out]
        }
    
    def prepare_swap_data(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        min_amount_out: float,
        recipient: str,
        hidden_hash: Optional[str] = None
    ) -> Dict:
        """
        Prepara datos para ejecutar un swap
        
        Args:
            token_in: Token de entrada
            token_out: Token de salida
            amount_in: Cantidad de entrada
            min_amount_out: Cantidad mínima de salida
            recipient: Destinatario
            hidden_hash: Hash de transacción invisible (opcional)
            
        Returns:
            Dict con datos del swap
        """
        # Preparar hookData si hay transacción invisible
        hook_data = "0x"
        if hidden_hash:
            # Codificar hidden_hash y flag isInvisible
            # En producción, usar abi.encode de Web3
            hook_data = self.encode_invisible_swap_data(hidden_hash)
        
        return {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "min_amount_out": min_amount_out,
            "recipient": recipient,
            "hook_data": hook_data,
            "deadline": self.w3.eth.get_block('latest')['timestamp'] + 1800  # 30 minutos
        }
    
    def encode_invisible_swap_data(self, hidden_hash: str) -> str:
        """
        Codifica datos para swap invisible
        
        Args:
            hidden_hash: Hash de la transacción invisible
            
        Returns:
            Datos codificados en hexadecimal
        """
        # Convertir hash a bytes32
        hash_bytes = bytes.fromhex(hidden_hash[2:] if hidden_hash.startswith('0x') else hidden_hash)
        
        # Codificar: (bytes32 hiddenHash, bool isInvisible)
        # En producción, usar abi.encode real
        is_invisible = True
        
        # Simulación simple de encoding
        encoded = f"0x{hash_bytes.hex()}{'01' if is_invisible else '00'}"
        
        return encoded
    
    def get_pool_info(self, token0: str, token1: str, fee: int = 3000) -> Dict:
        """
        Obtiene información de un pool de Uniswap v4
        
        Args:
            token0: Primera dirección de token
            token1: Segunda dirección de token
            fee: Fee tier (3000 = 0.3%)
            
        Returns:
            Dict con información del pool
        """
        # En producción, consultar PoolManager real
        return {
            "token0": token0,
            "token1": token1,
            "fee": fee,
            "liquidity": 1000000000000000000,  # Simulado
            "sqrt_price_x96": 79228162514264337593543950336,  # Simulado
            "tick": 0
        }
    
    def estimate_gas_for_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: float
    ) -> int:
        """
        Estima gas para un swap
        
        Returns:
            Gas estimado
        """
        # Estimación base
        base_gas = 150000
        
        # Si hay hook, agregar gas adicional
        if self.hook_address:
            base_gas += 50000
        
        return base_gas
    
    def get_contract_abi(self, contract_name: str) -> list:
        """
        Obtiene el ABI de un contrato
        
        Args:
            contract_name: Nombre del contrato
            
        Returns:
            ABI como lista
        """
        # En producción, leer desde archivos o API
        abis = {
            "InvisibleTransfer": [],
            "UniswapV4Hook": [],
            "TokenWrapper": []
        }
        
        return abis.get(contract_name, [])
    
    def check_allowance(
        self,
        token_address: str,
        owner: str,
        spender: str
    ) -> int:
        """
        Verifica el allowance de un token
        
        Args:
            token_address: Dirección del token
            owner: Propietario de los tokens
            spender: Dirección autorizada a gastar
            
        Returns:
            Allowance actual
        """
        # ABI mínimo de ERC20 para allowance
        erc20_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            allowance = token_contract.functions.allowance(
                Web3.to_checksum_address(owner),
                Web3.to_checksum_address(spender)
            ).call()
            
            return allowance
        except Exception as e:
            print(f"Error checking allowance: {e}")
            return 0
