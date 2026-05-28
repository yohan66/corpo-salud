from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from config import Config

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # user, admin, superuser
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assets_registered = db.relationship('Asset', backref='registered_by_user', foreign_keys='Asset.registered_by', lazy=True)
    assets_updated = db.relationship('Asset', backref='updated_by_user', foreign_keys='Asset.updated_by', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

class Category(db.Model):
    """Asset category classification"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    code = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assets = db.relationship('Asset', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Location(db.Model):
    """Location/Department where assets are stored"""
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)  # DEPARTMENT, OFFICE, ROOM, WAREHOUSE
    code = db.Column(db.String(20), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Location', remote_side=[id], backref='sublocations')
    assets = db.relationship('Asset', backref='location', lazy=True)
    
    def __repr__(self):
        return f'<Location {self.name}>'

class Brand(db.Model):
    """Brand/Manufacturer of assets"""
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    country = db.Column(db.String(100))
    website = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assets = db.relationship('Asset', backref='brand', lazy=True, primaryjoin='Brand.id==Asset.brand_id')
    
    def __repr__(self):
        return f'<Brand {self.name}>'

class Supplier(db.Model):
    """Supplier/Provider of assets"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    rif = db.Column(db.String(20), unique=True)  # Tax ID
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    contact_person = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class Asset(db.Model):
    """Main asset model"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    asset_type = db.Column(db.String(20), nullable=False)  # ESTADAL or NACIONAL
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    serial_number = db.Column(db.String(100), unique=True)
    rfid_tag = db.Column(db.String(100), unique=True)
    
    # Description
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    model = db.Column(db.String(100))
    
    # Classification
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    
    # Acquisition
    acquisition_date = db.Column(db.Date)
    purchase_price = db.Column(db.Numeric(15, 2))
    invoice_number = db.Column(db.String(50))
    warranty_expiry = db.Column(db.Date)
    
    # Location
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    assigned_to = db.Column(db.String(200))  # Person or department responsible
    
    # Status
    status = db.Column(db.String(20), nullable=False, default=Config.STATUS_ACTIVE)
    condition = db.Column(db.String(50))  # NEW, GOOD, FAIR, POOR
    is_operational = db.Column(db.Boolean, default=True)
    
    # Technical specifications
    specifications = db.Column(db.JSON)  # Flexible JSON field for different asset types
    
    # Audit trail
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_records = db.relationship('MaintenanceRecord', backref='asset', lazy=True)
    transfers = db.relationship('AssetTransfer', backref='asset', lazy=True)
    images = db.relationship('AssetImage', backref='asset', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Asset {self.barcode}: {self.name}>'
    
    @property
    def age_years(self):
        if self.acquisition_date:
            delta = datetime.now().date() - self.acquisition_date
            return round(delta.days / 365.25, 1)
        return 0
    
    @property
    def is_under_warranty(self):
        if self.warranty_expiry:
            return self.warranty_expiry >= datetime.now().date()
        return False

class MaintenanceRecord(db.Model):
    """Maintenance and repair history"""
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # PREVENTIVE, CORRECTIVE, INSPECTION
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    performed_by = db.Column(db.String(200))
    cost = db.Column(db.Numeric(10, 2))
    date = db.Column(db.Date, nullable=False)
    next_maintenance = db.Column(db.Date)
    status = db.Column(db.String(20), default='COMPLETED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Maintenance {self.type}: {self.title}>'

class AssetTransfer(db.Model):
    """Record of asset transfers between locations"""
    __tablename__ = 'asset_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    to_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    transferred_by = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text)
    transfer_date = db.Column(db.Date, nullable=False)
    authorized_by = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    from_location = db.relationship('Location', foreign_keys=[from_location_id])
    to_location = db.relationship('Location', foreign_keys=[to_location_id])
    
    def __repr__(self):
        return f'<Transfer {self.asset_id}: {self.transfer_date}>'

class Purchase(db.Model):
    """Purchase order records"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(15, 2))
    status = db.Column(db.String(20), default='PENDING')  # PENDING, RECEIVED, CANCELLED
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Purchase {self.order_number}>'

class AssetImage(db.Model):
    """Asset photographs"""
    __tablename__ = 'asset_images'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssetImage {self.filename}>'

class AuditLog(db.Model):
    """System audit log"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action}: {self.entity_type}>'

# Initialize database
def init_db(app):
    """Initialize database with application context"""
    with app.app_context():
        db.create_all()
        # Create default categories if not exist
        default_categories = [
            {'name': 'Computadoras', 'code': 'CAT-001', 'description': 'Equipos de cómputo personales y portátiles'},
            {'name': 'Servidores', 'code': 'CAT-002', 'description': 'Equipos servidores de red y datos'},
            {'name': 'Impresoras', 'code': 'CAT-003', 'description': 'Impresoras, escáneres y multifuncionales'},
            {'name': 'Redes', 'code': 'CAT-004', 'description': 'Routers, switches, cables y equipos de red'},
            {'name': 'Monitores', 'code': 'CAT-005', 'description': 'Pantallas y monitores de visualización'},
            {'name': 'Telefonía', 'code': 'CAT-006', 'description': 'Teléfonos, centrales y equipos de comunicación'},
            {'name': 'Software', 'code': 'CAT-007', 'description': 'Licencias y software instalado'},
            {'name': 'Muebles', 'code': 'CAT-008', 'description': 'Mobiliario de oficina y estaciones de trabajo'},
            {'name': 'Vehículos', 'code': 'CAT-009', 'description': 'Vehículos institucionales'},
            {'name': 'Equipo Médico', 'code': 'CAT-010', 'description': 'Equipos y dispositivos médicos'}
        ]
        
        for cat_data in default_categories:
            if not Category.query.filter_by(code=cat_data['code']).first():
                category = Category(**cat_data)
                db.session.add(category)
        
        # Create default locations for Technical Support Department
        default_locations = [
            {'name': 'Soporte Técnico - Oficina Principal', 'type': 'DEPARTMENT', 'code': 'LOC-ST-001'},
            {'name': 'Sala de Servidores', 'type': 'ROOM', 'code': 'LOC-ST-002'},
            {'name': 'Almacén de Soporte', 'type': 'WAREHOUSE', 'code': 'LOC-ST-003'},
            {'name': 'Piso 1 - Estaciones de Trabajo', 'type': 'ROOM', 'code': 'LOC-FL1-001'},
            {'name': 'Piso 2 - Estaciones de Trabajo', 'type': 'ROOM', 'code': 'LOC-FL2-001'},
        ]
        
        for loc_data in default_locations:
            if not Location.query.filter_by(code=loc_data['code']).first():
                location = Location(**loc_data)
                db.session.add(location)
        
        # Create default admin user
        if not User.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@corp-salud-tachira.gob.ve',
                password=generate_password_hash('Admin2024!', method='scrypt'),
                full_name='Administrador del Sistema',
                role='superuser',
                is_active=True
            )
            db.session.add(admin)
        
        db.session.commit()
        print('Database initialized successfully!')