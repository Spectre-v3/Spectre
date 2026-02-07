from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Base para modelos
Base = declarative_base()

class Transaction(Base):
    """Modelo de transacción en base de datos"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, unique=True, index=True, nullable=False)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    token = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, claimed, cancelled
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class User(Base):
    """Modelo de usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_sent = Column(Integer, default=0)
    total_received = Column(Integer, default=0)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invisible_transfers.db")

# Crear engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Generador de sesiones de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    """Manejador de operaciones de base de datos"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_transaction(
        self,
        hash: str,
        sender: str,
        recipient: str,
        amount: float,
        token: str,
        salt: str,
        timestamp: int
    ) -> Transaction:
        """Crea una nueva transacción en la base de datos"""
        db = self.SessionLocal()
        try:
            tx = Transaction(
                hash=hash,
                sender=sender.lower(),
                recipient=recipient.lower(),
                amount=amount,
                token=token.upper(),
                salt=salt,
                timestamp=timestamp,
                status="pending"
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx
        finally:
            db.close()
    
    def get_transaction_by_hash(self, hash: str) -> Transaction:
        """Obtiene una transacción por su hash"""
        db = self.SessionLocal()
        try:
            return db.query(Transaction).filter(Transaction.hash == hash).first()
        finally:
            db.close()
    
    def get_pending_transactions_for_recipient(self, recipient: str) -> list:
        """Obtiene transacciones pendientes para un destinatario"""
        db = self.SessionLocal()
        try:
            return db.query(Transaction).filter(
                Transaction.recipient == recipient.lower(),
                Transaction.status == "pending"
            ).all()
        finally:
            db.close()
    
    def mark_transaction_claimed(self, hash: str) -> bool:
        """Marca una transacción como reclamada"""
        db = self.SessionLocal()
        try:
            tx = db.query(Transaction).filter(Transaction.hash == hash).first()
            if tx and tx.status == "pending":
                tx.status = "claimed"
                tx.claimed_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def get_user_stats(self, address: str) -> dict:
        """Obtiene estadísticas de un usuario"""
        db = self.SessionLocal()
        try:
            sent = db.query(Transaction).filter(
                Transaction.sender == address.lower()
            ).count()
            
            received = db.query(Transaction).filter(
                Transaction.recipient == address.lower(),
                Transaction.status == "claimed"
            ).count()
            
            return {
                "address": address,
                "total_sent": sent,
                "total_received": received
            }
        finally:
            db.close()
    
    def get_all_transactions(self, limit: int = 100) -> list:
        """Obtiene todas las transacciones con límite"""
        db = self.SessionLocal()
        try:
            return db.query(Transaction).order_by(
                Transaction.created_at.desc()
            ).limit(limit).all()
        finally:
            db.close()
    
    def ensure_user_exists(self, address: str) -> User:
        """Asegura que un usuario exista en la base de datos"""
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.address == address.lower()).first()
            if not user:
                user = User(address=address.lower())
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                user.last_activity = datetime.utcnow()
                db.commit()
            return user
        finally:
            db.close()
