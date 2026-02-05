"""Wallet domain repository - database operations for wallets and tokens."""

from datetime import datetime
from typing import Optional, List
from beanie import PydanticObjectId
from src.guzo.wallet.core import (
    DriverWallet,
    TokenTransaction,
    TokenPackage,
    PlatformFeeConfig,
    TokenTransactionType,
)
from src.guzo.infrastructure.repository import BaseRepository


class WalletRepository(BaseRepository[DriverWallet]):
    """Repository for DriverWallet database operations."""
    
    def __init__(self):
        super().__init__(DriverWallet)
    
    async def get_by_driver_id(self, driver_id: str) -> Optional[DriverWallet]:
        """Get wallet by driver ID."""
        return await DriverWallet.find_one(DriverWallet.driver_id == driver_id)
    
    async def get_or_create(self, driver_id: str) -> DriverWallet:
        """Get existing wallet or create a new one for driver."""
        wallet = await self.get_by_driver_id(driver_id)
        if not wallet:
            wallet = DriverWallet(driver_id=driver_id)
            await wallet.insert()
        return wallet
    
    async def update_balance_atomic(
        self,
        wallet_id: str,
        amount: int,
        transaction_type: TokenTransactionType,
        description: Optional[str] = None,
        payment_reference: Optional[str] = None,
        payment_amount_etb: Optional[float] = None,
        admin_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        booking_count: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[TokenTransaction]:
        """
        Atomically update wallet balance and create transaction record.
        
        Args:
            wallet_id: The wallet ID
            amount: Positive for credit, negative for debit
            transaction_type: Type of transaction
            description: Human-readable description
            payment_reference: For purchases - receipt/bank ref
            payment_amount_etb: For purchases - amount paid
            admin_id: For purchases - who processed
            trip_id: For trip fees - which trip
            booking_count: For trip fees - number of bookings
            notes: Additional notes
            
        Returns:
            TokenTransaction if successful, None if insufficient balance for debits
        """
        wallet = await DriverWallet.get(PydanticObjectId(wallet_id))
        if not wallet:
            return None
        
        # For debits, check balance
        if amount < 0 and wallet.token_balance + amount < 0:
            return None
        
        # Update balance
        new_balance = wallet.token_balance + amount
        
        # Update lifetime stats
        if amount > 0:
            if transaction_type == TokenTransactionType.PURCHASE:
                wallet.total_purchased += amount
            elif transaction_type == TokenTransactionType.BONUS:
                wallet.total_bonus += amount
        elif amount < 0:
            wallet.total_spent += abs(amount)
        
        wallet.token_balance = new_balance
        wallet.updated_at = datetime.utcnow()
        await wallet.save()
        
        # Create transaction record
        transaction = TokenTransaction(
            driver_id=wallet.driver_id,
            wallet_id=str(wallet.id),
            transaction_type=transaction_type,
            amount=amount,
            balance_after=new_balance,
            description=description,
            payment_reference=payment_reference,
            payment_amount_etb=payment_amount_etb,
            admin_id=admin_id,
            trip_id=trip_id,
            booking_count=booking_count,
            notes=notes,
        )
        await transaction.insert()
        
        return transaction
    
    async def get_low_balance_wallets(self) -> List[DriverWallet]:
        """Get all wallets with balance below their threshold."""
        # Use aggregation to compare balance with threshold
        wallets = await DriverWallet.find(
            DriverWallet.is_active == True
        ).to_list()
        return [w for w in wallets if w.is_low_balance]
    
    async def get_all_active(self) -> List[DriverWallet]:
        """Get all active wallets."""
        return await DriverWallet.find(
            DriverWallet.is_active == True
        ).to_list()


class TransactionRepository(BaseRepository[TokenTransaction]):
    """Repository for TokenTransaction database operations."""
    
    def __init__(self):
        super().__init__(TokenTransaction)
    
    async def get_by_driver_id(
        self,
        driver_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[TokenTransaction]:
        """Get transaction history for a driver."""
        return await TokenTransaction.find(
            TokenTransaction.driver_id == driver_id
        ).sort("-created_at").skip(offset).limit(limit).to_list()
    
    async def get_by_type(
        self,
        driver_id: str,
        transaction_type: TokenTransactionType,
        limit: int = 50
    ) -> List[TokenTransaction]:
        """Get transactions of a specific type for a driver."""
        return await TokenTransaction.find(
            TokenTransaction.driver_id == driver_id,
            TokenTransaction.transaction_type == transaction_type
        ).sort("-created_at").limit(limit).to_list()
    
    async def get_by_date_range(
        self,
        driver_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TokenTransaction]:
        """Get transactions within a date range."""
        return await TokenTransaction.find(
            TokenTransaction.driver_id == driver_id,
            TokenTransaction.created_at >= start_date,
            TokenTransaction.created_at < end_date
        ).sort("-created_at").to_list()
    
    async def get_recent_purchases(
        self,
        limit: int = 50
    ) -> List[TokenTransaction]:
        """Get recent purchase transactions (for admin)."""
        return await TokenTransaction.find(
            TokenTransaction.transaction_type == TokenTransactionType.PURCHASE
        ).sort("-created_at").limit(limit).to_list()
    
    async def count_by_driver(self, driver_id: str) -> int:
        """Count total transactions for a driver."""
        return await TokenTransaction.find(
            TokenTransaction.driver_id == driver_id
        ).count()


class PackageRepository(BaseRepository[TokenPackage]):
    """Repository for TokenPackage database operations."""
    
    def __init__(self):
        super().__init__(TokenPackage)
    
    async def get_active_packages(self) -> List[TokenPackage]:
        """Get all active token packages sorted by sort_order."""
        return await TokenPackage.find(
            TokenPackage.is_active == True
        ).sort("+sort_order").to_list()
    
    async def get_by_name(self, name: str) -> Optional[TokenPackage]:
        """Get package by name."""
        return await TokenPackage.find_one(TokenPackage.name == name)


class FeeConfigRepository:
    """Repository for PlatformFeeConfig operations."""
    
    async def get_active(self) -> Optional[PlatformFeeConfig]:
        """Get the active fee configuration."""
        return await PlatformFeeConfig.find_one(
            PlatformFeeConfig.is_active == True
        )
    
    async def get_or_create_default(self) -> PlatformFeeConfig:
        """Get active config or create default."""
        config = await self.get_active()
        if not config:
            config = PlatformFeeConfig()
            await config.insert()
        return config
    
    async def update(self, updates: dict) -> PlatformFeeConfig:
        """Update the active fee configuration."""
        config = await self.get_or_create_default()
        
        for key, value in updates.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        await config.save()
        return config


# Singleton instances
wallet_repository = WalletRepository()
transaction_repository = TransactionRepository()
package_repository = PackageRepository()
fee_config_repository = FeeConfigRepository()
