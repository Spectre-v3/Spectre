# API Reference - Spectre Backend

Base URL: `http://localhost:8000`

## Endpoints

### Health Check

**GET** `/health`

Verifica el estado del servidor.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T12:00:00.000000"
}
```

---

### Generate Hash

**POST** `/api/generate-hash`

Genera un hash único para una transacción invisible.

**Request Body**
```json
{
  "sender": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "recipient": "0x5B38Da6a701c568545dCfcB03FcB875f56beddC4",
  "amount": 100.5,
  "token": "USDC"
}
```

**Response**
```json
{
  "hash": "0xabc123...",
  "salt": "a1b2c3d4...",
  "timestamp": 1707312000,
  "sender": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "recipient": "0x5b38da6a701c568545dcfcb03fcb875f56beddc4",
  "amount": 100.5,
  "token": "USDC",
  "status": "pending"
}
```

**Errors**
- `400 Bad Request`: Dirección Ethereum inválida
- `500 Internal Server Error`: Error generando hash

---

### Verify Transaction

**POST** `/api/verify-transaction`

Verifica si un hash corresponde a un destinatario específico.

**Request Body**
```json
{
  "hash": "0xabc123...",
  "recipient": "0x5B38Da6a701c568545dCfcB03FcB875f56beddC4"
}
```

**Response**
```json
{
  "valid": true,
  "hash": "0xabc123...",
  "amount": 100.5,
  "token": "USDC",
  "message": "Transaction is valid for this recipient"
}
```

---

### Transaction Status

**GET** `/api/transaction-status/{hash}`

Obtiene el estado de una transacción.

**Parameters**
- `hash` (path): Hash de la transacción

**Response**
```json
{
  "hash": "0xabc123...",
  "status": "pending",
  "sender": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "amount": 100.5,
  "token": "USDC",
  "timestamp": 1707312000,
  "claimed_at": null
}
```

**Status Values**
- `pending`: Transacción publicada, no reclamada
- `claimed`: Transacción reclamada
- `cancelled`: Transacción cancelada

**Errors**
- `404 Not Found`: Transacción no encontrada

---

### Pending Transfers

**GET** `/api/pending-transfers/{address}`

Obtiene transacciones pendientes para una dirección.

**Parameters**
- `address` (path): Dirección Ethereum del destinatario

**Response**
```json
{
  "address": "0x5b38da6a701c568545dcfcb03fcb875f56beddc4",
  "count": 2,
  "transactions": [
    {
      "hash": "0xabc123...",
      "sender": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
      "amount": 100.5,
      "token": "USDC",
      "timestamp": 1707312000,
      "created_at": "2026-02-07T12:00:00"
    }
  ]
}
```

**Errors**
- `400 Bad Request`: Dirección Ethereum inválida

---

### Claim Transaction

**POST** `/api/claim-transaction`

Marca una transacción como reclamada (debe llamarse después del claim on-chain).

**Request Body**
```json
{
  "hash": "0xabc123...",
  "claimer": "0x5B38Da6a701c568545dCfcB03FcB875f56beddC4"
}
```

**Response**
```json
{
  "success": true,
  "hash": "0xabc123...",
  "claimer": "0x5b38da6a701c568545dcfcb03fcb875f56beddc4",
  "message": "Transaction claimed successfully"
}
```

**Errors**
- `400 Bad Request`: No se pudo reclamar la transacción
- `403 Forbidden`: El claimer no es el destinatario
- `500 Internal Server Error`: Error reclamando transacción

---

### Uniswap Quote

**POST** `/api/uniswap/quote`

Obtiene una cotización de Uniswap v4.

**Request Body**
```json
{
  "token_in": "0x...",
  "token_out": "0x...",
  "amount_in": 100.0,
  "decimals_in": 18
}
```

**Response**
```json
{
  "token_in": "0x...",
  "token_out": "0x...",
  "amount_in": "100000000000000000000",
  "amount_out_estimated": "98000000000000000000",
  "price_impact": 2.0,
  "gas_estimated": 150000,
  "route": ["0x...", "0x..."]
}
```

---

### System Stats

**GET** `/api/stats`

Obtiene estadísticas generales del sistema.

**Response**
```json
{
  "total_transactions": 156,
  "pending_transactions": 23,
  "claimed_transactions": 133,
  "timestamp": "2026-02-07T12:00:00.000000"
}
```

---

### User Stats

**GET** `/api/user-stats/{address}`

Obtiene estadísticas de un usuario específico.

**Parameters**
- `address` (path): Dirección Ethereum del usuario

**Response**
```json
{
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "total_sent": 45,
  "total_received": 32
}
```

**Errors**
- `400 Bad Request`: Dirección Ethereum inválida

---

## Error Responses

Todos los endpoints pueden devolver estos errores:

### 400 Bad Request
```json
{
  "detail": "Invalid Ethereum address"
}
```

### 404 Not Found
```json
{
  "detail": "Transaction not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error generating hash: <mensaje de error>"
}
```

---

## Rate Limiting

Actualmente no hay rate limiting implementado. En producción se recomienda:
- 100 requests/minuto por IP
- 1000 requests/hora por usuario

---

## Authentication

Actualmente no hay autenticación. En producción se recomienda:
- JWT tokens
- API keys para clientes
- OAuth 2.0 para integraciones

---

## Websockets (Futuro)

Planeado para notificaciones en tiempo real:

```javascript
ws://localhost:8000/ws/{userAddress}

// Eventos
{
  "type": "transaction_received",
  "data": {
    "hash": "0x...",
    "amount": 100.5,
    "token": "USDC"
  }
}
```

---

## Ejemplos de Uso

### JavaScript (fetch)

```javascript
// Generar hash
const response = await fetch('http://localhost:8000/api/generate-hash', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    sender: walletAddress,
    recipient: recipientAddress,
    amount: 100.0,
    token: 'USDC'
  })
});

const data = await response.json();
console.log('Hash:', data.hash);
```

### Python (requests)

```python
import requests

response = requests.post(
    'http://localhost:8000/api/generate-hash',
    json={
        'sender': '0x...',
        'recipient': '0x...',
        'amount': 100.0,
        'token': 'USDC'
    }
)

data = response.json()
print('Hash:', data['hash'])
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/generate-hash" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0x...",
    "recipient": "0x...",
    "amount": 100.0,
    "token": "USDC"
  }'
```
