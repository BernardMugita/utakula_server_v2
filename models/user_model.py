from email.policy import default
import uuid
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from passlib.context import CryptContext
from models.models import Base

# Configure the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginType:
    PASSWORD = "password"
    GOOGLE_OAUTH = "google_oauth"
    BOTH = "both"
 
class UserModel(Base):
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name='user_id'
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    _password_hash: Mapped[str] = mapped_column(String(100), name="password", nullable=True)
    device_token: Mapped[str] = mapped_column(String(255), nullable=True)
    
    #google oauth fields
    google_oauth_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    login_type: Mapped[LoginType] = mapped_column(String(20), nullable=False, default=LoginType.PASSWORD)

    # Relationships
    meal_plan = relationship("MealPlanModel", back_populates="user", uselist=False)
    notifications = relationship("NotificationModel", back_populates="user", uselist=False)
    metrics = relationship("UserMetricsModel", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, username: str, email: str, password: str = None, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
            
        self.role = kwargs.get('role', 'user')
        self.device_token = kwargs.get('device_token')
        self.google_oauth_id = kwargs.get('google_oauth_id')
        
        if self.google_oauth_id and password:
            self.login_type = LoginType.BOTH
        elif self.google_oauth_id:
            self.login_type = LoginType.GOOGLE_OAUTH
        else:
            self.login_type = LoginType.PASSWORD

    def set_password(self, password: str):
        """Hashes and stores the user's password."""
        self._password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verifies the provided password against the stored hash."""
        return pwd_context.verify(password, self._password_hash)