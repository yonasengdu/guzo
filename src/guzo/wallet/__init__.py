"""Wallet module - Token-based payment system for drivers."""

from src.guzo.wallet.core import (
    # Enums
    TokenTransactionType,
    # Models
    DriverWallet,
    TokenTransaction,
    TokenPackage,
    PlatformFeeConfig,
    # Response schemas
    WalletResponse,
    TransactionResponse,
    PackageResponse,
    FeeConfigResponse,
    # Request schemas
    PurchaseTokensRequest,
    ManualCreditRequest,
    CreatePackageRequest,
    UpdatePackageRequest,
    UpdateFeeConfigRequest,
    UpdateWalletSettingsRequest,
)
from src.guzo.wallet.service import WalletService, InsufficientTokensError
from src.guzo.wallet.repository import (
    WalletRepository,
    TransactionRepository,
    PackageRepository,
    FeeConfigRepository,
    wallet_repository,
    transaction_repository,
    package_repository,
    fee_config_repository,
)
from src.guzo.wallet.resource import router

__all__ = [
    # Enums
    "TokenTransactionType",
    # Models
    "DriverWallet",
    "TokenTransaction",
    "TokenPackage",
    "PlatformFeeConfig",
    # Response schemas
    "WalletResponse",
    "TransactionResponse",
    "PackageResponse",
    "FeeConfigResponse",
    # Request schemas
    "PurchaseTokensRequest",
    "ManualCreditRequest",
    "CreatePackageRequest",
    "UpdatePackageRequest",
    "UpdateFeeConfigRequest",
    "UpdateWalletSettingsRequest",
    # Service
    "WalletService",
    "InsufficientTokensError",
    # Repositories
    "WalletRepository",
    "TransactionRepository",
    "PackageRepository",
    "FeeConfigRepository",
    "wallet_repository",
    "transaction_repository",
    "package_repository",
    "fee_config_repository",
    # Router
    "router",
]
