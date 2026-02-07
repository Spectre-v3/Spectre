/**
 * wallet.js - Gestión de conexión con MetaMask y wallet
 */

class WalletManager {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.userAddress = null;
        this.network = null;
        this.isConnected = false;
    }

    /**
     * Verifica si MetaMask está instalado
     */
    isMetaMaskInstalled() {
        return typeof window.ethereum !== 'undefined';
    }

    /**
     * Conecta con MetaMask
     */
    async connect() {
        if (!this.isMetaMaskInstalled()) {
            showToast('MetaMask no está instalado. Por favor instálalo primero.', 'error');
            window.open('https://metamask.io/download/', '_blank');
            return false;
        }

        try {
            showLoading('Conectando con MetaMask...');

            // Solicitar acceso a las cuentas
            await window.ethereum.request({ method: 'eth_requestAccounts' });

            // Crear provider y signer
            this.provider = new ethers.providers.Web3Provider(window.ethereum);
            this.signer = this.provider.getSigner();
            this.userAddress = await this.signer.getAddress();
            this.network = await this.provider.getNetwork();
            this.isConnected = true;

            // Escuchar cambios de cuenta
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.handleAccountChanged(accounts[0]);
                }
            });

            // Escuchar cambios de red
            window.ethereum.on('chainChanged', () => {
                window.location.reload();
            });

            hideLoading();
            showToast('Wallet conectada exitosamente', 'success');
            
            return true;

        } catch (error) {
            hideLoading();
            console.error('Error connecting wallet:', error);
            
            if (error.code === 4001) {
                showToast('Conexión rechazada por el usuario', 'warning');
            } else {
                showToast('Error al conectar wallet: ' + error.message, 'error');
            }
            
            return false;
        }
    }

    /**
     * Maneja el cambio de cuenta
     */
    async handleAccountChanged(newAccount) {
        this.userAddress = newAccount;
        showToast('Cuenta cambiada', 'info');
        window.location.reload();
    }

    /**
     * Desconecta la wallet
     */
    disconnect() {
        this.provider = null;
        this.signer = null;
        this.userAddress = null;
        this.isConnected = false;
        showToast('Wallet desconectada', 'info');
        updateUIDisconnected();
    }

    /**
     * Obtiene el balance de ETH del usuario
     */
    async getBalance() {
        if (!this.isConnected) return '0';

        try {
            const balance = await this.provider.getBalance(this.userAddress);
            return ethers.utils.formatEther(balance);
        } catch (error) {
            console.error('Error getting balance:', error);
            return '0';
        }
    }

    /**
     * Obtiene el balance de un token ERC20
     */
    async getTokenBalance(tokenAddress, decimals = 18) {
        if (!this.isConnected) return '0';

        try {
            const tokenContract = new ethers.Contract(
                tokenAddress,
                ['function balanceOf(address) view returns (uint256)'],
                this.provider
            );

            const balance = await tokenContract.balanceOf(this.userAddress);
            return ethers.utils.formatUnits(balance, decimals);
        } catch (error) {
            console.error('Error getting token balance:', error);
            return '0';
        }
    }

    /**
     * Verifica y solicita allowance para un token
     */
    async checkAndApproveToken(tokenAddress, spenderAddress, amount, decimals = 18) {
        if (!this.isConnected) {
            throw new Error('Wallet not connected');
        }

        try {
            const tokenContract = new ethers.Contract(
                tokenAddress,
                [
                    'function allowance(address owner, address spender) view returns (uint256)',
                    'function approve(address spender, uint256 amount) returns (bool)'
                ],
                this.signer
            );

            // Verificar allowance actual
            const currentAllowance = await tokenContract.allowance(
                this.userAddress,
                spenderAddress
            );

            const amountInWei = ethers.utils.parseUnits(amount.toString(), decimals);

            // Si el allowance es suficiente, no hacer nada
            if (currentAllowance.gte(amountInWei)) {
                return true;
            }

            // Solicitar aprobación
            showLoading('Aprobando tokens...');
            const tx = await tokenContract.approve(spenderAddress, amountInWei);
            await tx.wait();
            hideLoading();

            showToast('Tokens aprobados exitosamente', 'success');
            return true;

        } catch (error) {
            hideLoading();
            console.error('Error approving tokens:', error);
            throw error;
        }
    }

    /**
     * Obtiene la información de la red actual
     */
    async getNetworkInfo() {
        if (!this.isConnected) return null;

        const network = await this.provider.getNetwork();
        const networkNames = {
            1: 'Ethereum Mainnet',
            5: 'Goerli Testnet',
            11155111: 'Sepolia Testnet',
            137: 'Polygon Mainnet',
            80001: 'Mumbai Testnet'
        };

        return {
            chainId: network.chainId,
            name: networkNames[network.chainId] || 'Unknown Network'
        };
    }

    /**
     * Cambia a una red específica
     */
    async switchNetwork(chainId) {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: ethers.utils.hexValue(chainId) }],
            });
            return true;
        } catch (error) {
            console.error('Error switching network:', error);
            
            // Si la red no está agregada, intentar agregarla
            if (error.code === 4902) {
                showToast('Red no encontrada. Por favor agrégala manualmente.', 'warning');
            } else {
                showToast('Error al cambiar de red', 'error');
            }
            
            return false;
        }
    }

    /**
     * Formatea una dirección para mostrarla
     */
    formatAddress(address, chars = 4) {
        if (!address) return '';
        return `${address.substring(0, chars + 2)}...${address.substring(42 - chars)}`;
    }

    /**
     * Verifica si una dirección es válida
     */
    isValidAddress(address) {
        try {
            return ethers.utils.isAddress(address);
        } catch {
            return false;
        }
    }
}

// Instancia global del wallet manager
const walletManager = new WalletManager();
