from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import uvicorn
from datetime import datetime

from crypto_utils import (
    PrivacyEngine, 
    validate_ethereum_address,
    generate_salt,
    hash_data
)
from database import (
    init_db, 
    DatabaseManager, 
    get_db,
    Transaction
)
from uniswap_client import UniswapClient

# Inicializar FastAPI
app = FastAPI(
    title="Invisible Transfer API",
    description="API para transacciones invisibles en blockchain con Uniswap v4",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
privacy_engine = PrivacyEngine()
db_manager = DatabaseManager()
uniswap_client = UniswapClient()

# Inicializar BD al arrancar
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized")
    print("✅ Privacy Engine ready")
    print("✅ Uniswap Client initialized")

# Modelos Pydantic
class GenerateHashRequest(BaseModel):
    sender: str = Field(..., description="Dirección Ethereum del remitente")
    recipient: str = Field(..., description="Dirección Ethereum del destinatario")
    amount: float = Field(..., gt=0, description="Cantidad de tokens")
    token: str = Field(..., description="Símbolo o dirección del token")
    
    @validator('sender', 'recipient')
    def validate_address(cls, v):
        if not validate_ethereum_address(v):
            raise ValueError('Invalid Ethereum address')
        return v.lower()

class GenerateHashResponse(BaseModel):
    hash: str
    salt: str
    timestamp: int
    sender: str
    recipient: str
    amount: float
    token: str
    status: str

class VerifyTransactionRequest(BaseModel):
    hash: str
    recipient: str
    
    @validator('recipient')
    def validate_recipient(cls, v):
        if not validate_ethereum_address(v):
            raise ValueError('Invalid Ethereum address')
        return v.lower()

class TransactionStatusResponse(BaseModel):
    hash: str
    status: str
    sender: Optional[str]
    amount: Optional[float]
    token: Optional[str]
    timestamp: Optional[int]
    claimed_at: Optional[datetime]

class UniswapQuoteRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in: float
    decimals_in: int = 18

class ClaimTransactionRequest(BaseModel):
    hash: str
    claimer: str
    
    @validator('claimer')
    def validate_claimer(cls, v):
        if not validate_ethereum_address(v):
            raise ValueError('Invalid Ethereum address')
        return v.lower()

# Endpoints

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": "Invisible Transfer API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "generate_hash": "/api/generate-hash",
            "verify_transaction": "/api/verify-transaction",
            "transaction_status": "/api/transaction-status/{hash}",
            "pending_transfers": "/api/pending-transfers/{address}",
            "uniswap_quote": "/api/uniswap/quote",
            "stats": "/api/stats"
        }
    }

@app.post("/api/generate-hash", response_model=GenerateHashResponse)
async def generate_hash(request: GenerateHashRequest):
    """
    Genera un hash único para una transacción invisible
    
    - **sender**: Dirección del remitente
    - **recipient**: Dirección del destinatario  
    - **amount**: Cantidad de tokens
    - **token**: Símbolo del token (USDC, ETH, etc.)
    """
    try:
        # Generar transacción oculta
        result = privacy_engine.generate_hidden_transaction(
            sender=request.sender,
            recipient=request.recipient,
            amount=request.amount,
            token=request.token
        )
        
        # Guardar en base de datos
        db_manager.create_transaction(
            hash=result["hash"],
            sender=request.sender,
            recipient=request.recipient,
            amount=request.amount,
            token=request.token,
            salt=result["salt"],
            timestamp=result["timestamp"]
        )
        
        # Asegurar que los usuarios existan
        db_manager.ensure_user_exists(request.sender)
        db_manager.ensure_user_exists(request.recipient)
        
        return GenerateHashResponse(
            hash=result["hash"],
            salt=result["salt"],
            timestamp=result["timestamp"],
            sender=request.sender,
            recipient=request.recipient,
            amount=request.amount,
            token=request.token,
            status=result["status"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating hash: {str(e)}")

@app.post("/api/verify-transaction")
async def verify_transaction(request: VerifyTransactionRequest):
    """
    Verifica si un hash corresponde a un destinatario específico
    
    - **hash**: Hash de la transacción
    - **recipient**: Dirección del destinatario a verificar
    """
    try:
        is_valid = privacy_engine.verify_recipient(
            transaction_hash=request.hash,
            recipient=request.recipient
        )
        
        if is_valid:
            # Obtener detalles de la transacción
            tx_details = privacy_engine.get_transaction_details(request.hash)
            
            return {
                "valid": True,
                "hash": request.hash,
                "amount": tx_details.get("amount") if tx_details else None,
                "token": tx_details.get("token") if tx_details else None,
                "message": "Transaction is valid for this recipient"
            }
        else:
            return {
                "valid": False,
                "hash": request.hash,
                "message": "Transaction not found or not for this recipient"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying transaction: {str(e)}")

@app.get("/api/transaction-status/{hash}", response_model=TransactionStatusResponse)
async def get_transaction_status(hash: str):
    """
    Obtiene el estado de una transacción por su hash
    
    - **hash**: Hash de la transacción
    """
    try:
        # Buscar en base de datos
        tx = db_manager.get_transaction_by_hash(hash)
        
        if not tx:
            # Buscar en engine
            tx_details = privacy_engine.get_transaction_details(hash)
            if not tx_details:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return TransactionStatusResponse(
                hash=hash,
                status=tx_details["status"],
                sender=tx_details.get("sender"),
                amount=tx_details.get("amount"),
                token=tx_details.get("token"),
                timestamp=tx_details.get("timestamp"),
                claimed_at=None
            )
        
        return TransactionStatusResponse(
            hash=tx.hash,
            status=tx.status,
            sender=tx.sender,
            amount=tx.amount,
            token=tx.token,
            timestamp=tx.timestamp,
            claimed_at=tx.claimed_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transaction status: {str(e)}")

@app.get("/api/pending-transfers/{address}")
async def get_pending_transfers(address: str):
    """
    Obtiene todas las transacciones pendientes para una dirección
    
    - **address**: Dirección Ethereum del destinatario
    """
    try:
        # Validar dirección
        if not validate_ethereum_address(address):
            raise HTTPException(status_code=400, detail="Invalid Ethereum address")
        
        address = address.lower()
        
        # Obtener de base de datos
        pending_txs = db_manager.get_pending_transactions_for_recipient(address)
        
        # Formatear respuesta
        result = []
        for tx in pending_txs:
            result.append({
                "hash": tx.hash,
                "sender": tx.sender,
                "amount": tx.amount,
                "token": tx.token,
                "timestamp": tx.timestamp,
                "created_at": tx.created_at.isoformat()
            })
        
        return {
            "address": address,
            "count": len(result),
            "transactions": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pending transfers: {str(e)}")

@app.post("/api/claim-transaction")
async def claim_transaction(request: ClaimTransactionRequest):
    """
    Marca una transacción como reclamada (llamar después de reclamo on-chain)
    
    - **hash**: Hash de la transacción
    - **claimer**: Dirección que reclama
    """
    try:
        # Verificar que el claimer es el destinatario
        is_valid = privacy_engine.verify_recipient(request.hash, request.claimer)
        
        if not is_valid:
            raise HTTPException(
                status_code=403, 
                detail="Claimer is not the recipient of this transaction"
            )
        
        # Marcar como reclamada en engine
        success = privacy_engine.mark_as_claimed(request.hash, request.claimer)
        
        if not success:
            raise HTTPException(status_code=400, detail="Could not claim transaction")
        
        # Marcar en base de datos
        db_manager.mark_transaction_claimed(request.hash)
        
        return {
            "success": True,
            "hash": request.hash,
            "claimer": request.claimer,
            "message": "Transaction claimed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error claiming transaction: {str(e)}")

@app.post("/api/uniswap/quote")
async def get_uniswap_quote(request: UniswapQuoteRequest):
    """
    Obtiene una cotización de Uniswap v4 para un swap
    
    - **token_in**: Dirección del token de entrada
    - **token_out**: Dirección del token de salida
    - **amount_in**: Cantidad de tokens de entrada
    - **decimals_in**: Decimales del token de entrada
    """
    try:
        quote = uniswap_client.get_quote(
            token_in=request.token_in,
            token_out=request.token_out,
            amount_in=request.amount_in,
            decimals_in=request.decimals_in
        )
        
        return quote
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting quote: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """
    Obtiene estadísticas generales del sistema
    """
    try:
        # Stats del privacy engine
        engine_stats = privacy_engine.get_stats()
        
        return {
            "total_transactions": engine_stats["total_transactions"],
            "pending_transactions": engine_stats["total_pending"],
            "claimed_transactions": engine_stats["total_claimed"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/api/user-stats/{address}")
async def get_user_stats(address: str):
    """
    Obtiene estadísticas de un usuario específico
    
    - **address**: Dirección Ethereum del usuario
    """
    try:
        # Validar dirección
        if not validate_ethereum_address(address):
            raise HTTPException(status_code=400, detail="Invalid Ethereum address")
        
        stats = db_manager.get_user_stats(address)
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user stats: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Ejecutar servidor
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
