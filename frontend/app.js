/**
 * app.js - Lógica principal de la aplicación
 */

// Dirección del contrato desplegado (actualizar después del deployment)
const INVISIBLE_TRANSFER_CONTRACT = '0x...'; // Actualizar con dirección real

// ABI del contrato (solo las funciones que necesitamos)
const INVISIBLE_TRANSFER_ABI = [
    'function publishHiddenTransfer(bytes32 _hash, address _token, uint256 _amount) external payable',
    'function claimHiddenTransfer(bytes32 _hash) external',
    'function getHiddenTransfer(bytes32 _hash) external view returns (address sender, address token, uint256 amount, uint256 timestamp, bool claimed)',
    'function getUserSentTransfers(address user) external view returns (bytes32[] memory)',
    'function getUserReceivedTransfers(address user) external view returns (bytes32[] memory)',
    'event TransferPublished(bytes32 indexed hash, address indexed sender, address token, uint256 amount)',
    'event TransferClaimed(bytes32 indexed hash, address indexed recipient, uint256 amount)'
];

// Estado global de la aplicación
let appState = {
    contract: null,
    pendingTransactions: [],
    sentTransactions: [],
    receivedTransactions: [],
    currentFilter: 'all'
};

/**
 * Inicializa la aplicación cuando carga la página
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando Spectre...');
    
    // Configurar event listeners
    setupEventListeners();
    
    // Verificar si ya hay una wallet conectada
    if (walletManager.isMetaMaskInstalled()) {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
            await handleWalletConnect();
        }
    }
    
    // Verificar estado del backend
    checkBackendHealth();
});

/**
 * Configura todos los event listeners
 */
function setupEventListeners() {
    // Botón de conexión de wallet
    document.getElementById('connectWalletBtn').addEventListener('click', handleWalletConnect);
    
    // Formulario de envío
    document.getElementById('sendForm').addEventListener('submit', handleSendTransaction);
    
    // Botón de refrescar pendientes
    document.getElementById('refreshPendingBtn').addEventListener('click', loadPendingTransactions);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Filtros de historial
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.target.dataset.filter;
            filterHistory(filter);
        });
    });
}

/**
 * Maneja la conexión de la wallet
 */
async function handleWalletConnect() {
    const connected = await walletManager.connect();
    
    if (connected) {
        // Actualizar UI
        updateUIConnected();
        
        // Inicializar contrato
        initializeContract();
        
        // Cargar datos del usuario
        await loadUserData();
    }
}

/**
 * Actualiza la UI cuando la wallet está conectada
 */
function updateUIConnected() {
    const connectBtn = document.getElementById('connectWalletBtn');
    const walletInfo = document.getElementById('walletInfo');
    const walletAddress = document.getElementById('walletAddress');
    const walletBalance = document.getElementById('walletBalance');
    
    connectBtn.classList.add('hidden');
    walletInfo.classList.remove('hidden');
    
    walletAddress.textContent = walletManager.formatAddress(walletManager.userAddress);
    
    // Actualizar balance
    walletManager.getBalance().then(balance => {
        walletBalance.textContent = `${parseFloat(balance).toFixed(4)} ETH`;
    });
}

/**
 * Actualiza la UI cuando la wallet está desconectada
 */
function updateUIDisconnected() {
    const connectBtn = document.getElementById('connectWalletBtn');
    const walletInfo = document.getElementById('walletInfo');
    
    connectBtn.classList.remove('hidden');
    walletInfo.classList.add('hidden');
}

/**
 * Inicializa el contrato inteligente
 */
function initializeContract() {
    if (!walletManager.isConnected) return;
    
    try {
        appState.contract = new ethers.Contract(
            INVISIBLE_TRANSFER_CONTRACT,
            INVISIBLE_TRANSFER_ABI,
            walletManager.signer
        );
        
        console.log('✅ Contrato inicializado');
        
        // Escuchar eventos del contrato
        listenToContractEvents();
    } catch (error) {
        console.error('Error inicializando contrato:', error);
        showToast('Error al inicializar contrato', 'error');
    }
}

/**
 * Escucha eventos del contrato
 */
function listenToContractEvents() {
    if (!appState.contract) return;
    
    // Evento de transferencia publicada
    appState.contract.on('TransferPublished', (hash, sender, token, amount) => {
        if (sender.toLowerCase() === walletManager.userAddress.toLowerCase()) {
            showToast('Transferencia publicada en blockchain', 'success');
            loadUserData();
        }
    });
    
    // Evento de transferencia reclamada
    appState.contract.on('TransferClaimed', (hash, recipient, amount) => {
        if (recipient.toLowerCase() === walletManager.userAddress.toLowerCase()) {
            showToast('Transferencia reclamada exitosamente', 'success');
            loadUserData();
        }
    });
}

/**
 * Maneja el envío de una transacción invisible
 */
async function handleSendTransaction(e) {
    e.preventDefault();
    
    if (!walletManager.isConnected) {
        showToast('Por favor conecta tu wallet primero', 'warning');
        return;
    }
    
    const recipient = document.getElementById('recipientAddress').value;
    const amount = document.getElementById('amount').value;
    const tokenSymbol = document.getElementById('tokenSelect').value;
    
    // Validaciones
    if (!walletManager.isValidAddress(recipient)) {
        showToast('Dirección de destinatario inválida', 'error');
        return;
    }
    
    if (parseFloat(amount) <= 0) {
        showToast('El monto debe ser mayor a cero', 'error');
        return;
    }
    
    try {
        showLoading('Generando hash invisible...');
        
        // 1. Generar hash en el backend
        const hashData = await apiClient.generateHash(
            walletManager.userAddress,
            recipient,
            amount,
            tokenSymbol
        );
        
        console.log('Hash generado:', hashData);
        
        // 2. Obtener dirección del token
        const tokenAddress = getTokenAddress(tokenSymbol);
        if (!tokenAddress) {
            throw new Error('Token no soportado');
        }
        
        // 3. Convertir amount a unidades del token
        const decimals = getTokenDecimals(tokenSymbol);
        const amountInWei = ethers.utils.parseUnits(amount, decimals);
        
        // 4. Aprobar tokens si es necesario
        showLoading('Aprobando tokens...');
        await walletManager.checkAndApproveToken(
            tokenAddress,
            INVISIBLE_TRANSFER_CONTRACT,
            amount,
            decimals
        );
        
        // 5. Publicar transacción en blockchain
        showLoading('Publicando transacción invisible...');
        const tx = await appState.contract.publishHiddenTransfer(
            hashData.hash,
            tokenAddress,
            amountInWei
        );
        
        showLoading('Esperando confirmación...');
        const receipt = await tx.wait();
        
        hideLoading();
        
        console.log('Transacción confirmada:', receipt);
        
        // Mostrar resultado
        displayTransactionResult(hashData, receipt);
        
        // Limpiar formulario
        document.getElementById('sendForm').reset();
        
        // Actualizar datos
        await loadUserData();
        
    } catch (error) {
        hideLoading();
        console.error('Error enviando transacción:', error);
        
        let message = 'Error al enviar transacción';
        if (error.code === 'ACTION_REJECTED') {
            message = 'Transacción rechazada por el usuario';
        } else if (error.message) {
            message = error.message;
        }
        
        showToast(message, 'error');
    }
}

/**
 * Muestra el resultado de una transacción
 */
function displayTransactionResult(hashData, receipt) {
    const resultDiv = document.getElementById('transactionResult');
    const hashElement = document.getElementById('resultHash');
    const explorerLink = document.getElementById('explorerLink');
    
    hashElement.textContent = hashData.hash;
    
    // Configurar link del explorer según la red
    const networkId = walletManager.network.chainId;
    const explorerUrls = {
        1: 'https://etherscan.io/tx/',
        5: 'https://goerli.etherscan.io/tx/',
        11155111: 'https://sepolia.etherscan.io/tx/',
        137: 'https://polygonscan.com/tx/',
        80001: 'https://mumbai.polygonscan.com/tx/'
    };
    
    const baseUrl = explorerUrls[networkId] || 'https://etherscan.io/tx/';
    explorerLink.href = baseUrl + receipt.transactionHash;
    
    resultDiv.classList.remove('hidden');
    
    // Scroll hacia el resultado
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Carga datos del usuario
 */
async function loadUserData() {
    if (!walletManager.isConnected) return;
    
    try {
        // Cargar estadísticas
        await loadUserStats();
        
        // Cargar transacciones pendientes
        await loadPendingTransactions();
        
        // Cargar historial
        await loadTransactionHistory();
        
    } catch (error) {
        console.error('Error cargando datos del usuario:', error);
    }
}

/**
 * Carga estadísticas del usuario
 */
async function loadUserStats() {
    try {
        const stats = await apiClient.getUserStats(walletManager.userAddress);
        
        document.getElementById('totalSent').textContent = stats.total_sent || 0;
        document.getElementById('totalReceived').textContent = stats.total_received || 0;
        
        // Cargar pendientes desde backend
        const pending = await apiClient.getPendingTransfers(walletManager.userAddress);
        document.getElementById('totalPending').textContent = pending.count || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Carga transacciones pendientes
 */
async function loadPendingTransactions() {
    if (!walletManager.isConnected) return;
    
    try {
        showLoading('Cargando transacciones pendientes...');
        
        const data = await apiClient.getPendingTransfers(walletManager.userAddress);
        appState.pendingTransactions = data.transactions || [];
        
        displayPendingTransactions();
        
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Error loading pending transactions:', error);
        showToast('Error al cargar transacciones pendientes', 'error');
    }
}

/**
 * Muestra transacciones pendientes en la UI
 */
function displayPendingTransactions() {
    const container = document.getElementById('pendingTransactions');
    
    if (appState.pendingTransactions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No hay transacciones pendientes</p>
                <small>Las transacciones aparecerán aquí cuando alguien te envíe fondos</small>
            </div>
        `;
        return;
    }
    
    container.innerHTML = appState.pendingTransactions.map(tx => `
        <div class="transaction-item">
            <div class="transaction-header">
                <div>
                    <div class="transaction-amount">${tx.amount} ${tx.token}</div>
                </div>
            </div>
            <div class="transaction-details">
                <div class="transaction-detail">
                    <label>De:</label>
                    <span>${walletManager.formatAddress(tx.sender, 6)}</span>
                </div>
                <div class="transaction-detail">
                    <label>Fecha:</label>
                    <span>${new Date(tx.created_at).toLocaleString()}</span>
                </div>
                <div class="transaction-detail">
                    <label>Hash:</label>
                    <span>${tx.hash.substring(0, 10)}...</span>
                </div>
            </div>
            <div class="transaction-actions">
                <button class="btn btn-primary" onclick="claimTransaction('${tx.hash}')">
                    💰 Reclamar
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Reclama una transacción
 */
async function claimTransaction(hash) {
    if (!walletManager.isConnected || !appState.contract) {
        showToast('Por favor conecta tu wallet', 'warning');
        return;
    }
    
    try {
        showLoading('Reclamando transacción...');
        
        // Llamar al contrato para reclamar
        const tx = await appState.contract.claimHiddenTransfer(hash);
        
        showLoading('Esperando confirmación...');
        await tx.wait();
        
        // Marcar como reclamada en el backend
        await apiClient.claimTransaction(hash, walletManager.userAddress);
        
        hideLoading();
        showToast('Transacción reclamada exitosamente', 'success');
        
        // Recargar datos
        await loadUserData();
        
    } catch (error) {
        hideLoading();
        console.error('Error claiming transaction:', error);
        
        let message = 'Error al reclamar transacción';
        if (error.code === 'ACTION_REJECTED') {
            message = 'Transacción rechazada por el usuario';
        } else if (error.message) {
            message = error.message;
        }
        
        showToast(message, 'error');
    }
}

/**
 * Carga el historial de transacciones
 */
async function loadTransactionHistory() {
    if (!walletManager.isConnected) return;
    
    try {
        // En una implementación real, obtener del backend o del contrato
        // Por ahora, mostrar mensaje vacío
        const container = document.getElementById('transactionHistory');
        container.innerHTML = `
            <div class="empty-state">
                <p>No hay transacciones en el historial</p>
            </div>
        `;
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

/**
 * Cambia entre tabs
 */
function switchTab(tabName) {
    // Remover active de todos los botones y contenidos
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Activar el tab seleccionado
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Cargar datos según el tab
    if (tabName === 'receive') {
        loadPendingTransactions();
    } else if (tabName === 'history') {
        loadTransactionHistory();
    }
}

/**
 * Filtra el historial
 */
function filterHistory(filter) {
    appState.currentFilter = filter;
    
    // Actualizar botones
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.filter-btn[data-filter="${filter}"]`).classList.add('active');
    
    // Aplicar filtro (implementar según necesidad)
    loadTransactionHistory();
}

/**
 * Copia el hash al portapapeles
 */
function copyHash() {
    const hash = document.getElementById('resultHash').textContent;
    navigator.clipboard.writeText(hash).then(() => {
        showToast('Hash copiado al portapapeles', 'success');
    });
}

/**
 * Verifica la salud del backend
 */
async function checkBackendHealth() {
    try {
        await apiClient.healthCheck();
        console.log('✅ Backend conectado');
    } catch (error) {
        console.warn('⚠️ Backend no disponible:', error);
        showToast('Backend no disponible. Algunas funciones pueden no funcionar.', 'warning');
    }
}

// ===================================
// UTILIDADES UI
// ===================================

/**
 * Muestra overlay de carga
 */
function showLoading(message = 'Cargando...') {
    const overlay = document.getElementById('loadingOverlay');
    const text = document.getElementById('loadingText');
    text.textContent = message;
    overlay.classList.remove('hidden');
}

/**
 * Oculta overlay de carga
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('hidden');
}

/**
 * Muestra una notificación toast
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Remover después de 5 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
