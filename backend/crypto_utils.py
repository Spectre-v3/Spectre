import hashlib
import secrets
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class HiddenTransaction:
    """Representa una transacción oculta con toda su metadata"""
    sender: str
    recipient: str
    amount: float
    token: str
    salt: str
    timestamp: int
    hash: str
    status: str = "pending"  # pending, claimed, cancelled

class PrivacyEngine:
    """Motor principal para generación y validación de transacciones invisibles"""
    
    def __init__(self):
        self.pending_transactions: Dict[str, HiddenTransaction] = {}
        self.claimed_transactions: Dict[str, HiddenTransaction] = {}
    
    def generate_hidden_transaction(
        self, 
        sender: str, 
        recipient: str, 
        amount: float, 
        token: str
    ) -> Dict:
        """
        Genera una transacción oculta con hash único usando SHA-256
        
        Args:
            sender: Dirección del remitente (0x...)
            recipient: Dirección del destinatario (0x...)
            amount: Cantidad de tokens
            token: Símbolo o dirección del token
            
        Returns:
            Dict con hash, salt, timestamp y otros datos
        """
        # Generar salt criptográficamente seguro
        salt = secrets.token_hex(32)  # 64 caracteres hex
        timestamp = int(time.time())
        
        # Crear payload para hash
        # Formato: sender:recipient:amount:token:salt:timestamp
        payload = f"{sender.lower()}:{recipient.lower()}:{amount}:{token.upper()}:{salt}:{timestamp}"
        
        # Generar hash SHA-256
        transaction_hash = hashlib.sha256(payload.encode()).hexdigest()
        
        # Convertir a formato 0x para compatibilidad con blockchain
        transaction_hash_hex = f"0x{transaction_hash}"
        
        # Crear objeto de transacción oculta
        hidden_tx = HiddenTransaction(
            sender=sender.lower(),
            recipient=recipient.lower(),
            amount=amount,
            token=token.upper(),
            salt=salt,
            timestamp=timestamp,
            hash=transaction_hash_hex,
            status="pending"
        )
        
        # Almacenar en pendientes
        self.pending_transactions[transaction_hash_hex] = hidden_tx
        
        return {
            "hash": transaction_hash_hex,
            "salt": salt,
            "timestamp": timestamp,
            "sender": sender.lower(),
            "amount": amount,
            "token": token.upper(),
            "status": "pending"
        }
    
    def verify_recipient(self, transaction_hash: str, recipient: str) -> bool:
        """
        Verifica si un hash corresponde a un destinatario específico
        
        Args:
            transaction_hash: Hash de la transacción
            recipient: Dirección del destinatario a verificar
            
        Returns:
            True si el hash pertenece al destinatario
        """
        if transaction_hash not in self.pending_transactions:
            # Verificar también en reclamadas
            if transaction_hash in self.claimed_transactions:
                return False  # Ya fue reclamada
            return False
        
        tx = self.pending_transactions[transaction_hash]
        return tx.recipient.lower() == recipient.lower()
    
    def verify_transaction_data(
        self,
        transaction_hash: str,
        sender: str,
        recipient: str,
        amount: float,
        token: str,
        salt: str,
        timestamp: int
    ) -> bool:
        """
        Verifica que un hash corresponde exactamente a los datos proporcionados
        """
        # Recrear payload
        payload = f"{sender.lower()}:{recipient.lower()}:{amount}:{token.upper()}:{salt}:{timestamp}"
        
        # Generar hash
        computed_hash = f"0x{hashlib.sha256(payload.encode()).hexdigest()}"
        
        return computed_hash == transaction_hash
    
    def get_pending_for_recipient(self, recipient: str) -> list:
        """
        Obtiene todas las transacciones pendientes para un destinatario
        
        Args:
            recipient: Dirección del destinatario
            
        Returns:
            Lista de transacciones pendientes
        """
        pending = []
        for hash_key, tx in self.pending_transactions.items():
            if tx.recipient.lower() == recipient.lower() and tx.status == "pending":
                # No revelar todos los datos, solo lo necesario
                pending.append({
                    "hash": tx.hash,
                    "amount": tx.amount,
                    "token": tx.token,
                    "timestamp": tx.timestamp,
                    "sender": tx.sender  # En producción, esto también se ocultaría
                })
        return pending
    
    def mark_as_claimed(self, transaction_hash: str, claimer: str) -> bool:
        """
        Marca una transacción como reclamada
        
        Args:
            transaction_hash: Hash de la transacción
            claimer: Dirección que reclama
            
        Returns:
            True si se marcó exitosamente
        """
        if transaction_hash not in self.pending_transactions:
            return False
        
        tx = self.pending_transactions[transaction_hash]
        
        # Verificar que quien reclama es el destinatario
        if tx.recipient.lower() != claimer.lower():
            return False
        
        # Mover a reclamadas
        tx.status = "claimed"
        self.claimed_transactions[transaction_hash] = tx
        del self.pending_transactions[transaction_hash]
        
        return True
    
    def get_transaction_details(self, transaction_hash: str) -> Optional[Dict]:
        """
        Obtiene detalles completos de una transacción
        """
        # Buscar en pendientes
        if transaction_hash in self.pending_transactions:
            return asdict(self.pending_transactions[transaction_hash])
        
        # Buscar en reclamadas
        if transaction_hash in self.claimed_transactions:
            return asdict(self.claimed_transactions[transaction_hash])
        
        return None
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del sistema
        """
        return {
            "total_pending": len(self.pending_transactions),
            "total_claimed": len(self.claimed_transactions),
            "total_transactions": len(self.pending_transactions) + len(self.claimed_transactions)
        }

def generate_salt(length: int = 32) -> str:
    """
    Genera un salt criptográficamente seguro
    
    Args:
        length: Longitud del salt en bytes (se convertirá a hex, duplicando la longitud)
        
    Returns:
        Salt en formato hexadecimal
    """
    return secrets.token_hex(length)

def hash_data(data: str) -> str:
    """
    Genera hash SHA-256 de datos
    
    Args:
        data: Datos a hashear
        
    Returns:
        Hash en formato hexadecimal con prefijo 0x
    """
    return f"0x{hashlib.sha256(data.encode()).hexdigest()}"

def validate_ethereum_address(address: str) -> bool:
    """
    Valida formato de dirección Ethereum
    
    Args:
        address: Dirección a validar
        
    Returns:
        True si es válida
    """
    if not address:
        return False
    
    # Verificar formato básico
    if not address.startswith("0x"):
        return False
    
    if len(address) != 42:
        return False
    
    # Verificar que son caracteres hexadecimales
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False
