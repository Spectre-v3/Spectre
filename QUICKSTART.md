# Inicio Rápido - Spectre

## Setup en 5 Minutos

### 1. Prerequisitos
Asegúrate de tener instalado:
- Python 3.10+
- Node.js 18+
- Git
- MetaMask en tu navegador

### 2. Clonar e Instalar

```bash
# Clonar repositorio
git clone https://github.com/Spectre-v3/Spectre.git
cd Spectre

# Ejecutar script de deployment automático
chmod +x deploy.sh
./deploy.sh
```

### 3. Configurar Variables de Entorno

```bash
# Editar archivo .env del backend
cd backend
nano .env  # o usa tu editor favorito

# Agregar tu RPC URL (Infura, Alchemy, etc)
RPC_URL=https://sepolia.infura.io/v3/TU_API_KEY
```

### 4. Obtener Testnet Tokens

Para probar en Sepolia necesitas:

1. **ETH de Sepolia** (para gas):
   - https://sepoliafaucet.com/
   - https://www.infura.io/faucet/sepolia

2. **Tokens de Prueba** (USDC, DAI, etc):
   - Usar faucets de cada proyecto
   - O deployar tus propios tokens mock

### 5. Desplegar Contratos

```bash
cd contracts

# Desplegar en Sepolia
forge script scripts/Deploy.s.sol:DeployInvisibleTransfer \
  --rpc-url https://sepolia.infura.io/v3/TU_API_KEY \
  --private-key TU_PRIVATE_KEY \
  --broadcast --verify

# Copiar la dirección del contrato desplegado
# Ejemplo: InvisibleTransfer deployed at: 0x1234...
```

### 6. Actualizar Direcciones

**Frontend**: Editar `frontend/app.js`
```javascript
// Línea 5
const INVISIBLE_TRANSFER_CONTRACT = '0x1234...'; // Tu dirección
```

**Backend**: Editar `backend/.env`
```
INVISIBLE_TRANSFER_ADDRESS=0x1234...
```

### 7. Iniciar Servicios

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py

# Deberías ver:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 8080

# Deberías ver:
# Serving HTTP on 0.0.0.0 port 8080
```

### 8. Usar la Aplicación

1. Abrir navegador en `http://localhost:8080`
2. Conectar MetaMask
3. ¡Empezar a hacer transacciones invisibles!

---

## Primera Transacción de Prueba

### Enviar Tokens (Alice → Bob)

1. **Conectar Wallet** (Alice)
   - Clic en "Conectar Wallet"
   - Aprobar en MetaMask

2. **Crear Transacción Invisible**
   - Ir a tab "Enviar"
   - Ingresar dirección de Bob
   - Cantidad: 10
   - Token: USDC
   - Clic en "Crear Transacción Invisible"

3. **Aprobar en MetaMask**
   - Primera tx: Aprobar USDC
   - Segunda tx: Publicar transacción

4. **Copiar Hash**
   - Se mostrará un hash como: `0xabc123...`
   - Copiar para compartir con Bob

### Recibir Tokens (Bob)

1. **Conectar Wallet** (Bob)
   - Cambiar cuenta en MetaMask a la de Bob
   - Recargar página
   - Conectar wallet

2. **Ver Pendientes**
   - Ir a tab "Recibir"
   - Clic en "Actualizar"
   - Deberías ver la transacción de Alice

3. **Reclamar**
   - Clic en "Reclamar"
   - Aprobar en MetaMask
   - ¡Tokens recibidos!

---

## 🔍 Verificar en Blockchain

Ver tus transacciones en el explorador:

**Sepolia:** https://sepolia.etherscan.io/

Buscar:
- Tu dirección de wallet
- La dirección del contrato
- El hash de transacción

---

## 🐛 Troubleshooting Común

### ❌ Error: "Network mismatch"

**Solución:** Cambiar a Sepolia en MetaMask
1. Abrir MetaMask
2. Clic en dropdown de redes
3. Seleccionar "Sepolia test network"

### ❌ Error: "Insufficient funds for gas"

**Solución:** Obtener ETH de Sepolia
- https://sepoliafaucet.com/

### ❌ Error: "Backend no disponible"

**Solución:** Verificar que el backend esté corriendo
```bash
cd backend
source venv/bin/activate
python main.py
```

### ❌ Error: "Invalid token address"

**Solución:** Actualizar direcciones de tokens en `frontend/api.js`

### ❌ Transacciones no aparecen

**Solución:** Verificar que:
1. Backend esté corriendo
2. Base de datos esté inicializada
3. Dirección del contrato esté correcta

---

## 📊 Verificar que Todo Funciona

### Test Backend
```bash
# En el navegador
http://localhost:8000/docs

# Deberías ver la interfaz Swagger UI
```

### Test Contratos
```bash
cd contracts
forge test

# Todos los tests deberían pasar
```

### Test Frontend
```bash
# Abrir consola del navegador (F12)
# Escribir:
walletManager

# Deberías ver el objeto WalletManager
```

---

## 📚 Siguientes Pasos

Una vez que todo funciona:

1. ✅ Leer la [Guía de Desarrollo](DEVELOPMENT.md)
2. ✅ Explorar la [Referencia de API](API.md)
3. ✅ Revisar el código de los contratos
4. ✅ Personalizar el frontend
5. ✅ Agregar más features

---

## 💡 Tips Útiles

### Desarrollo Rápido

**Auto-reload Backend:**
```bash
uvicorn main:app --reload
```

**Live Server Frontend:**
```bash
npx serve frontend -l 8080
```

### Debugging

**Ver logs del backend:**
```bash
tail -f logs/app.log  # Si configuraste logging
```

**Consola del navegador:**
```javascript
// Ver estado actual
console.log(appState);
console.log(walletManager.userAddress);
```

### Limpiar y Reiniciar

```bash
# Limpiar base de datos
rm backend/*.db

# Limpiar compilación de contratos
cd contracts
forge clean
forge build
```

---

## 🆘 ¿Necesitas Ayuda?

- 📖 [README Principal](README.md)
- 🔧 [Guía de Desarrollo](DEVELOPMENT.md)
- 📡 [API Reference](API.md)
- 🐛 [GitHub Issues](https://github.com/Spectre-v3/Spectre/issues)

---

## ✅ Checklist de Verificación

Antes de reportar problemas, verifica:

- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] Foundry instalado
- [ ] MetaMask instalado
- [ ] En red Sepolia
- [ ] Tienes ETH de Sepolia
- [ ] Backend corriendo en :8000
- [ ] Frontend corriendo en :8080
- [ ] Contratos desplegados
- [ ] Direcciones actualizadas en código
- [ ] Variables de entorno configuradas

---

<p align="center">
  <strong>🎉 ¡Listo para usar Spectre!</strong>
  <br>
  Si todo funciona, comparte tu experiencia con el equipo
</p>
