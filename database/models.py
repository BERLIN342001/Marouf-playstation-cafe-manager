from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base
import enum


class StationStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    VODAFONE_CASH = "vodafone_cash"
    INSTAPAY = "instapay"
    BANK_CARD = "bank_card"
    WALLET = "wallet"


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TournamentStatus(str, enum.Enum):
    REGISTRATION = "registration"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmployeeRole(str, enum.Enum):
    ADMIN = "admin"
    CASHIER = "cashier"
    SUPERVISOR = "supervisor"


class ShiftType(str, enum.Enum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"


# ─── Customer ──────────────────────────────────────────────
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    age = Column(Integer, nullable=True)
    balance = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    sessions = relationship("Session", back_populates="customer")
    reservations = relationship("Reservation", back_populates="customer")
    tournament_participations = relationship("TournamentParticipant", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


# ─── Station ───────────────────────────────────────────────
class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    console_type = Column(String(20), nullable=False, default="PS5")
    status = Column(String(20), default=StationStatus.AVAILABLE.value)
    hourly_rate = Column(Float, default=30.0)
    has_vr = Column(Boolean, default=False)
    has_wheel = Column(Boolean, default=False)
    controller_count = Column(Integer, default=2)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    sessions = relationship("Session", back_populates="station")
    reservations = relationship("Reservation", back_populates="station")


# ─── Game ──────────────────────────────────────────────────
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    platform = Column(String(20), default="PS5")
    genre = Column(String(50), nullable=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    is_digital = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# ─── Session ───────────────────────────────────────────────
class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    total_cost = Column(Float, default=0.0)
    status = Column(String(20), default=SessionStatus.ACTIVE.value)
    is_package = Column(Boolean, default=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="sessions")
    station = relationship("Station", back_populates="sessions")
    package = relationship("Package")
    games = relationship("SessionGame", back_populates="session")
    payments = relationship("Payment", back_populates="session")


# ─── SessionGame ───────────────────────────────────────────
class SessionGame(Base):
    __tablename__ = "session_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    session = relationship("Session", back_populates="games")
    game = relationship("Game")


# ─── Payment ───────────────────────────────────────────────
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20), default=PaymentMethod.CASH.value)
    discount = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")


# ─── Package ───────────────────────────────────────────────
class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    hours = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# ─── InventoryItem ─────────────────────────────────────────
class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=5)
    unit_price = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── Employee ──────────────────────────────────────────────
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(String(20), default=EmployeeRole.CASHIER.value)
    shift = Column(String(20), default=ShiftType.MORNING.value)
    salary = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    attendance = relationship("Attendance", back_populates="employee")


# ─── Attendance ────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=True)
    date = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="attendance")


# ─── Reservation ───────────────────────────────────────────
class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    reserved_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(20), default=ReservationStatus.PENDING.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="reservations")
    station = relationship("Station", back_populates="reservations")


# ─── Tournament ────────────────────────────────────────────
class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    game = Column(String(100), nullable=False)
    max_players = Column(Integer, default=16)
    entry_fee = Column(Float, default=0.0)
    prize = Column(String(200), nullable=True)
    start_date = Column(DateTime, nullable=False)
    status = Column(String(20), default=TournamentStatus.REGISTRATION.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    participants = relationship("TournamentParticipant", back_populates="tournament")


# ─── TournamentParticipant ─────────────────────────────────
class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    bracket_position = Column(Integer, nullable=True)
    is_eliminated = Column(Boolean, default=False)
    rank = Column(Integer, nullable=True)

    tournament = relationship("Tournament", back_populates="participants")
    customer = relationship("Customer", back_populates="tournament_participations")


# ─── Setting ───────────────────────────────────────────────
class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())