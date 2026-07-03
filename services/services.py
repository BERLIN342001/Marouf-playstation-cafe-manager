from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, and_, or_
from database.models import (
    Customer, Station, Session as GameSession, Payment, Game, InventoryItem,
    Employee, Attendance, Reservation, Tournament, TournamentParticipant,
    Package, Setting, SessionGame, StationStatus, SessionStatus, PaymentMethod,
    ReservationStatus, TournamentStatus, EmployeeRole, ShiftType
)


# ════════════════════════════════════════════════════════════
#  UTILITY
# ════════════════════════════════════════════════════════════
def get_setting(db: DBSession, key: str, default: str = "") -> str:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else default


def set_setting(db: DBSession, key: str, value: str):
    s = db.query(Setting).filter(Setting.key == key).first()
    if s:
        s.value = value
    else:
        s = Setting(key=key, value=value)
        db.add(s)
    db.commit()


def get_hourly_rate(db: DBSession) -> float:
    try:
        return float(get_setting(db, "hourly_rate", "30"))
    except ValueError:
        return 30.0


# ════════════════════════════════════════════════════════════
#  CUSTOMER SERVICE
# ════════════════════════════════════════════════════════════
def create_customer(db: DBSession, name: str, phone: str, age: int = None, notes: str = None) -> Customer:
    customer = Customer(name=name, phone=phone, age=age, notes=notes)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customers(db: DBSession, search: str = "", active_only: bool = True):
    q = db.query(Customer)
    if active_only:
        q = q.filter(Customer.is_active == True)
    if search:
        q = q.filter(or_(
            Customer.name.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%")
        ))
    return q.order_by(Customer.created_at.desc()).all()


def get_customer_by_id(db: DBSession, customer_id: int) -> Customer:
    return db.query(Customer).filter(Customer.id == customer_id).first()


def update_customer(db: DBSession, customer_id: int, **kwargs) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return None
    for key, value in kwargs.items():
        if hasattr(customer, key) and value is not None:
            setattr(customer, key, value)
    customer.updated_at = datetime.now()
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: DBSession, customer_id: int) -> bool:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.is_active = False
        db.commit()
        return True
    return False


def charge_customer_balance(db: DBSession, customer_id: int, amount: float) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.balance += amount
        db.commit()
        db.refresh(customer)
    return customer


def add_customer_points(db: DBSession, customer_id: int, points: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.points += points
        db.commit()
        db.refresh(customer)
    return customer


# ════════════════════════════════════════════════════════════
#  STATION SERVICE
# ════════════════════════════════════════════════════════════
def create_station(db: DBSession, name: str, console_type: str = "PS5",
                   hourly_rate: float = None, has_vr: bool = False,
                   has_wheel: bool = False, controller_count: int = 2) -> Station:
    if hourly_rate is None:
        hourly_rate = get_hourly_rate(db)
    station = Station(
        name=name, console_type=console_type, hourly_rate=hourly_rate,
        has_vr=has_vr, has_wheel=has_wheel, controller_count=controller_count
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


def get_stations(db: DBSession, status: str = None, console_type: str = None):
    q = db.query(Station).filter(Station.is_active == True)
    if status:
        q = q.filter(Station.status == status)
    if console_type:
        q = q.filter(Station.console_type == console_type)
    return q.order_by(Station.id).all()


def get_station_by_id(db: DBSession, station_id: int) -> Station:
    return db.query(Station).filter(Station.id == station_id).first()


def update_station(db: DBSession, station_id: int, **kwargs) -> Station:
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return None
    for key, value in kwargs.items():
        if hasattr(station, key) and value is not None:
            setattr(station, key, value)
    db.commit()
    db.refresh(station)
    return station


def delete_station(db: DBSession, station_id: int) -> bool:
    station = db.query(Station).filter(Station.id == station_id).first()
    if station:
        station.is_active = False
        db.commit()
        return True
    return False


def get_station_stats(db: DBSession):
    stations = db.query(Station).filter(Station.is_active == True).all()
    total = len(stations)
    available = sum(1 for s in stations if s.status == StationStatus.AVAILABLE.value)
    occupied = sum(1 for s in stations if s.status == StationStatus.OCCUPIED.value)
    maintenance = sum(1 for s in stations if s.status == StationStatus.MAINTENANCE.value)
    reserved = sum(1 for s in stations if s.status == StationStatus.RESERVED.value)
    return {
        "total": total,
        "available": available,
        "occupied": occupied,
        "maintenance": maintenance,
        "reserved": reserved
    }


# ════════════════════════════════════════════════════════════
#  SESSION SERVICE
# ════════════════════════════════════════════════════════════
def start_session(db: DBSession, station_id: int, customer_id: int = None,
                  is_package: bool = False, package_id: int = None,
                  game_ids: list = None) -> GameSession:
    station = get_station_by_id(db, station_id)
    if not station:
        raise ValueError("المحطة غير موجودة")

    if station.status == StationStatus.OCCUPIED.value:
        raise ValueError("المحطة مشغولة بالفعل")

    session = GameSession(
        customer_id=customer_id,
        station_id=station_id,
        start_time=datetime.now(),
        status=SessionStatus.ACTIVE.value,
        is_package=is_package,
        package_id=package_id
    )
    db.add(session)

    if game_ids:
        for gid in game_ids:
            sg = SessionGame(session=session, game_id=gid)
            db.add(sg)

    station.status = StationStatus.OCCUPIED.value
    db.commit()
    db.refresh(session)
    return session


def end_session(db: DBSession, session_id: int) -> GameSession:
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise ValueError("الجلسة غير موجودة")

    session.end_time = datetime.now()
    duration = (session.end_time - session.start_time).total_seconds() / 60
    session.duration_minutes = int(duration)

    station = get_station_by_id(db, session.station_id)
    hourly = station.hourly_rate if station else get_hourly_rate(db)

    if session.is_package and session.package:
        session.total_cost = 0
    else:
        hours = session.duration_minutes / 60
        session.total_cost = round(hours * hourly, 2)

    session.status = SessionStatus.COMPLETED.value
    station.status = StationStatus.AVAILABLE.value
    db.commit()
    db.refresh(session)
    return session


def cancel_session(db: DBSession, session_id: int) -> GameSession:
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise ValueError("الجلسة غير موجودة")

    session.status = SessionStatus.CANCELLED.value
    station = get_station_by_id(db, session.station_id)
    if station:
        station.status = StationStatus.AVAILABLE.value
    db.commit()
    db.refresh(session)
    return session


def get_sessions(db: DBSession, status: str = None, date_from: datetime = None,
                 date_to: datetime = None, customer_id: int = None):
    q = db.query(GameSession)
    if status:
        q = q.filter(GameSession.status == status)
    if date_from:
        q = q.filter(GameSession.start_time >= date_from)
    if date_to:
        q = q.filter(GameSession.start_time <= date_to)
    if customer_id:
        q = q.filter(GameSession.customer_id == customer_id)
    return q.order_by(GameSession.start_time.desc()).all()


def get_active_sessions(db: DBSession):
    return db.query(GameSession).filter(
        GameSession.status == SessionStatus.ACTIVE.value
    ).order_by(GameSession.start_time.desc()).all()


def get_session_by_id(db: DBSession, session_id: int) -> GameSession:
    return db.query(GameSession).filter(GameSession.id == session_id).first()


# ════════════════════════════════════════════════════════════
#  PAYMENT SERVICE
# ════════════════════════════════════════════════════════════
def create_payment(db: DBSession, amount: float, payment_method: str = "cash",
                   session_id: int = None, customer_id: int = None,
                   discount: float = 0.0, notes: str = None) -> Payment:
    final = max(amount - discount, 0)
    payment = Payment(
        session_id=session_id, customer_id=customer_id,
        amount=amount, payment_method=payment_method,
        discount=discount, final_amount=final, notes=notes
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def process_session_payment(db: DBSession, session_id: int, payment_method: str,
                             discount: float = 0.0) -> Payment:
    session = get_session_by_id(db, session_id)
    if not session:
        raise ValueError("الجلسة غير موجودة")

    payment = create_payment(
        db=db, amount=session.total_cost, payment_method=payment_method,
        session_id=session.id, customer_id=session.customer_id, discount=discount
    )

    if session.customer_id and payment_method == "wallet":
        customer = get_customer_by_id(db, session.customer_id)
        if customer and customer.balance >= payment.final_amount:
            customer.balance -= payment.final_amount
            db.commit()

    points_earned = int(payment.final_amount / 10)
    if session.customer_id and points_earned > 0:
        add_customer_points(db, session.customer_id, points_earned)

    return payment


def get_payments(db: DBSession, date_from: datetime = None, date_to: datetime = None):
    q = db.query(Payment)
    if date_from:
        q = q.filter(Payment.created_at >= date_from)
    if date_to:
        q = q.filter(Payment.created_at <= date_to)
    return q.order_by(Payment.created_at.desc()).all()


def get_daily_revenue(db: DBSession, date: datetime = None):
    if date is None:
        date = datetime.now()
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    payments = db.query(Payment).filter(
        and_(Payment.created_at >= start, Payment.created_at <= end)
    ).all()
    total = sum(p.final_amount for p in payments)
    return total, payments


# ════════════════════════════════════════════════════════════
#  GAME SERVICE
# ════════════════════════════════════════════════════════════
def create_game(db: DBSession, name: str, platform: str = "PS5",
                genre: str = None, total_copies: int = 1,
                is_digital: bool = False, notes: str = None) -> Game:
    game = Game(
        name=name, platform=platform, genre=genre,
        total_copies=total_copies, available_copies=total_copies,
        is_digital=is_digital, notes=notes
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def get_games(db: DBSession, search: str = "", platform: str = None):
    q = db.query(Game)
    if search:
        q = q.filter(Game.name.ilike(f"%{search}%"))
    if platform:
        q = q.filter(Game.platform == platform)
    return q.order_by(Game.name).all()


def delete_game(db: DBSession, game_id: int) -> bool:
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        db.delete(game)
        db.commit()
        return True
    return False


# ════════════════════════════════════════════════════════════
#  INVENTORY SERVICE
# ════════════════════════════════════════════════════════════
def add_inventory_item(db: DBSession, name: str, category: str,
                       quantity: int, min_quantity: int = 5,
                       unit_price: float = 0.0, notes: str = None) -> InventoryItem:
    item = InventoryItem(
        name=name, category=category, quantity=quantity,
        min_quantity=min_quantity, unit_price=unit_price, notes=notes
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_inventory(db: DBSession, category: str = None, low_stock: bool = False):
    q = db.query(InventoryItem)
    if category:
        q = q.filter(InventoryItem.category == category)
    if low_stock:
        q = q.filter(InventoryItem.quantity <= InventoryItem.min_quantity)
    return q.order_by(InventoryItem.category, InventoryItem.name).all()


def update_inventory_quantity(db: DBSession, item_id: int, new_quantity: int) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item:
        item.quantity = new_quantity
        item.updated_at = datetime.now()
        db.commit()
        db.refresh(item)
    return item


def delete_inventory_item(db: DBSession, item_id: int) -> bool:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def get_low_stock_items(db: DBSession):
    return db.query(InventoryItem).filter(
        InventoryItem.quantity <= InventoryItem.min_quantity
    ).all()


# ════════════════════════════════════════════════════════════
#  EMPLOYEE SERVICE
# ════════════════════════════════════════════════════════════
def create_employee(db: DBSession, name: str, phone: str,
                    role: str = "cashier", shift: str = "morning",
                    salary: float = 0.0, notes: str = None) -> Employee:
    employee = Employee(
        name=name, phone=phone, role=role,
        shift=shift, salary=salary, notes=notes
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_employees(db: DBSession, role: str = None, active_only: bool = True):
    q = db.query(Employee)
    if active_only:
        q = q.filter(Employee.is_active == True)
    if role:
        q = q.filter(Employee.role == role)
    return q.order_by(Employee.name).all()


def get_employee_by_id(db: DBSession, employee_id: int) -> Employee:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def update_employee(db: DBSession, employee_id: int, **kwargs) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return None
    for key, value in kwargs.items():
        if hasattr(employee, key) and value is not None:
            setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: DBSession, employee_id: int) -> bool:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee:
        employee.is_active = False
        db.commit()
        return True
    return False


def check_in(db: DBSession, employee_id: int) -> Attendance:
    att = Attendance(employee_id=employee_id, check_in=datetime.now(), date=datetime.now())
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def check_out(db: DBSession, employee_id: int) -> Attendance:
    att = db.query(Attendance).filter(
        and_(Attendance.employee_id == employee_id, Attendance.check_out == None)
    ).order_by(Attendance.check_in.desc()).first()
    if att:
        att.check_out = datetime.now()
        db.commit()
        db.refresh(att)
    return att


def get_attendance(db: DBSession, employee_id: int = None, date: datetime = None):
    q = db.query(Attendance)
    if employee_id:
        q = q.filter(Attendance.employee_id == employee_id)
    if date:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        q = q.filter(and_(Attendance.date >= start, Attendance.date <= end))
    return q.order_by(Attendance.check_in.desc()).all()


# ════════════════════════════════════════════════════════════
#  RESERVATION SERVICE
# ════════════════════════════════════════════════════════════
def create_reservation(db: DBSession, customer_id: int, station_id: int,
                       reserved_date: datetime, duration_minutes: int = 60,
                       notes: str = None) -> Reservation:
    reservation = Reservation(
        customer_id=customer_id, station_id=station_id,
        reserved_date=reserved_date, duration_minutes=duration_minutes,
        status=ReservationStatus.PENDING.value, notes=notes
    )
    db.add(reservation)
    station = get_station_by_id(db, station_id)
    if station:
        station.status = StationStatus.RESERVED.value
    db.commit()
    db.refresh(reservation)
    return reservation


def get_reservations(db: DBSession, status: str = None):
    q = db.query(Reservation)
    if status:
        q = q.filter(Reservation.status == status)
    return q.order_by(Reservation.reserved_date).all()


def update_reservation_status(db: DBSession, reservation_id: int, status: str) -> Reservation:
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        return None
    old_status = res.status
    res.status = status

    if status == ReservationStatus.CANCELLED.value and old_status != ReservationStatus.CANCELLED.value:
        station = get_station_by_id(db, res.station_id)
        if station and station.status == StationStatus.RESERVED.value:
            active_res = db.query(Reservation).filter(
                and_(
                    Reservation.station_id == res.station_id,
                    Reservation.status == ReservationStatus.PENDING.value,
                    Reservation.id != res.id
                )
            ).first()
            station.status = StationStatus.AVAILABLE.value if not active_res else StationStatus.RESERVED.value

    if status == ReservationStatus.COMPLETED.value:
        station = get_station_by_id(db, res.station_id)
        if station and station.status == StationStatus.RESERVED.value:
            station.status = StationStatus.AVAILABLE.value

    db.commit()
    db.refresh(res)
    return res


def cancel_reservation(db: DBSession, reservation_id: int) -> bool:
    res = update_reservation_status(db, reservation_id, ReservationStatus.CANCELLED.value)
    return res is not None


# ════════════════════════════════════════════════════════════
#  TOURNAMENT SERVICE
# ════════════════════════════════════════════════════════════
def create_tournament(db: DBSession, name: str, game: str, max_players: int = 16,
                      entry_fee: float = 0.0, prize: str = None,
                      start_date: datetime = None) -> Tournament:
    if start_date is None:
        start_date = datetime.now() + timedelta(days=7)
    tournament = Tournament(
        name=name, game=game, max_players=max_players,
        entry_fee=entry_fee, prize=prize, start_date=start_date,
        status=TournamentStatus.REGISTRATION.value
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


def get_tournaments(db: DBSession, status: str = None):
    q = db.query(Tournament)
    if status:
        q = q.filter(Tournament.status == status)
    return q.order_by(Tournament.start_date.desc()).all()


def register_participant(db: DBSession, tournament_id: int, customer_id: int) -> TournamentParticipant:
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise ValueError("البطولة غير موجودة")

    count = db.query(TournamentParticipant).filter(
        TournamentParticipant.tournament_id == tournament_id
    ).count()

    if count >= tournament.max_players:
        raise ValueError("البطولة ممتلئة")

    existing = db.query(TournamentParticipant).filter(
        and_(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.customer_id == customer_id
        )
    ).first()
    if existing:
        raise ValueError("العميل مسجل بالفعل")

    participant = TournamentParticipant(
        tournament_id=tournament_id, customer_id=customer_id,
        bracket_position=count + 1
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def get_tournament_participants(db: DBSession, tournament_id: int):
    return db.query(TournamentParticipant).filter(
        TournamentParticipant.tournament_id == tournament_id
    ).order_by(TournamentParticipant.bracket_position).all()


def update_tournament_status(db: DBSession, tournament_id: int, status: str) -> Tournament:
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament:
        tournament.status = status
        db.commit()
        db.refresh(tournament)
    return tournament


def eliminate_participant(db: DBSession, participant_id: int) -> TournamentParticipant:
    p = db.query(TournamentParticipant).filter(TournamentParticipant.id == participant_id).first()
    if p:
        p.is_eliminated = True
        db.commit()
        db.refresh(p)
    return p


# ════════════════════════════════════════════════════════════
#  PACKAGE SERVICE
# ════════════════════════════════════════════════════════════
def create_package(db: DBSession, name: str, hours: float, price: float) -> Package:
    pkg = Package(name=name, hours=hours, price=price)
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def get_packages(db: DBSession, active_only: bool = True):
    q = db.query(Package)
    if active_only:
        q = q.filter(Package.is_active == True)
    return q.all()


def delete_package(db: DBSession, package_id: int) -> bool:
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if pkg:
        pkg.is_active = False
        db.commit()
        return True
    return False


# ════════════════════════════════════════════════════════════
#  REPORT SERVICE
# ════════════════════════════════════════════════════════════
def get_dashboard_stats(db: DBSession):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    today_revenue, _ = get_daily_revenue(db, now)

    active_count = db.query(GameSession).filter(
        GameSession.status == SessionStatus.ACTIVE.value
    ).count()

    today_sessions = db.query(GameSession).filter(
        and_(GameSession.start_time >= today_start, GameSession.start_time <= today_end)
    ).count()

    today_completed = db.query(GameSession).filter(
        and_(
            GameSession.status == SessionStatus.COMPLETED.value,
            GameSession.end_time >= today_start,
            GameSession.end_time <= today_end
        )
    ).all()
    today_hours = sum(s.duration_minutes or 0 for s in today_completed) / 60

    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    station_stats = get_station_stats(db)
    low_stock = len(get_low_stock_items(db))

    week_start = today_start - timedelta(days=7)
    week_payments = db.query(Payment).filter(
        Payment.created_at >= week_start
    ).all()
    week_revenue = sum(p.final_amount for p in week_payments)

    return {
        "today_revenue": round(today_revenue, 2),
        "week_revenue": round(week_revenue, 2),
        "active_sessions": active_count,
        "today_sessions": today_sessions,
        "today_hours": round(today_hours, 1),
        "total_customers": total_customers,
        "station_stats": station_stats,
        "low_stock": low_stock,
    }


def get_revenue_report(db: DBSession, days: int = 30):
    result = []
    for i in range(days - 1, -1, -1):
        date = datetime.now() - timedelta(days=i)
        revenue, payments = get_daily_revenue(db, date)
        sessions_count = db.query(GameSession).filter(
            and_(
                GameSession.start_time >= date.replace(hour=0, minute=0, second=0, microsecond=0),
                GameSession.start_time <= date.replace(hour=23, minute=59, second=59, microsecond=999999)
            )
        ).count()
        result.append({
            "date": date.strftime("%Y-%m-%d"),
            "revenue": round(revenue, 2),
            "sessions": sessions_count,
            "payments_count": len(payments)
        })
    return result


def get_station_usage_report(db: DBSession, days: int = 30):
    date_from = datetime.now() - timedelta(days=days)
    sessions = db.query(GameSession).filter(
        and_(
            GameSession.start_time >= date_from,
            GameSession.status.in_([SessionStatus.COMPLETED.value, SessionStatus.ACTIVE.value])
        )
    ).all()

    station_data = {}
    for s in sessions:
        sid = s.station_id
        if sid not in station_data:
            station_data[sid] = {"station_id": sid, "total_sessions": 0, "total_minutes": 0, "total_revenue": 0}
        station_data[sid]["total_sessions"] += 1
        station_data[sid]["total_minutes"] += s.duration_minutes or 0
        station_data[sid]["total_revenue"] += s.total_cost or 0

    return list(station_data.values())


def get_payment_method_report(db: DBSession, days: int = 30):
    date_from = datetime.now() - timedelta(days=days)
    payments = db.query(Payment).filter(Payment.created_at >= date_from).all()

    methods = {}
    for p in payments:
        m = p.payment_method
        if m not in methods:
            methods[m] = {"method": m, "count": 0, "total": 0}
        methods[m]["count"] += 1
        methods[m]["total"] += p.final_amount

    return list(methods.values())


def get_top_customers_report(db: DBSession, limit: int = 10):
    from sqlalchemy import func
    results = db.query(
        Customer.id, Customer.name, Customer.phone,
        func.count(GameSession.id).label("total_sessions"),
        func.sum(GameSession.total_cost).label("total_spent")
    ).outerjoin(GameSession).filter(
        Customer.is_active == True
    ).group_by(Customer.id).order_by(
        func.sum(GameSession.total_cost).desc()
    ).limit(limit).all()

    return [
        {
            "id": r.id, "name": r.name, "phone": r.phone,
            "total_sessions": r.total_sessions or 0,
            "total_spent": round(r.total_spent or 0, 2)
        }
        for r in results
    ]