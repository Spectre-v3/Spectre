// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../InvisibleTransfer.sol";

/**
 * @title DeployInvisibleTransfer
 * @dev Script para desplegar el contrato InvisibleTransfer
 */
contract DeployInvisibleTransfer is Script {
    function run() external {
        // Obtener private key del entorno
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Configuración
        uint256 platformFee = 50; // 0.5%
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Desplegar contrato
        InvisibleTransfer invisibleTransfer = new InvisibleTransfer(platformFee);
        
        console.log("InvisibleTransfer deployed at:", address(invisibleTransfer));
        console.log("Platform fee:", platformFee, "basis points");
        
        vm.stopBroadcast();
    }
}
