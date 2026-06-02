from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Asset, Category, Location, Brand, Supplier, MaintenanceRecord, AssetTransfer, Purchase, AssetImage, AuditLog, init_db
from config import Config
import os
from datetime import datetime, timedelta
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor
def inject_user():
    return {'current_user': current_user}

app.context_processor(inject_user)

# Create upload directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================
# DECORADOR PERSONALIZADO PARA CONTROL DE ACCESO POR ROLES
# ============================================================

def admin_required(f):
    """Decorator que requiere rol admin o superuser"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin():
            flash('No tiene permisos de administrador para acceder a esta función.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def superuser_required(f):
    """Decorator que requiere rol superuser (CONTROL TOTAL)"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        if not current_user.is_superuser():
            flash('Esta función requiere control total del sistema (Superuser).', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==========
# Routes
# ==========

@app.route('/')
def index():
    """Dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    total_assets = Asset.query.count()
    state_assets = Asset.query.filter_by(asset_type=Config.STATE_ASSET).count()
    national_assets = Asset.query.filter_by(asset_type=Config.NATIONAL_ASSET).count()
    active_assets = Asset.query.filter_by(status=Config.STATUS_ACTIVE).count()
    maintenance_assets = Asset.query.filter_by(status=Config.STATUS_MAINTENANCE).count()
    damaged_assets = Asset.query.filter_by(status=Config.STATUS_DAMAGED).count()
    lost_assets = Asset.query.filter_by(status=Config.STATUS_LOST).count()

    # Recent activities
    recent_transfers = AssetTransfer.query.order_by(AssetTransfer.transfer_date.desc()).limit(5).all()
    recent_maintenance = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).limit(5).all()

    # Assets by category
    categories = Category.query.filter_by(is_active=True).all()
    category_stats = []
    for cat in categories:
        count = Asset.query.filter_by(category_id=cat.id).count()
        if count > 0:
            category_stats.append({'name': cat.name, 'count': count})

    return render_template('dashboard.html',
                         total_assets=total_assets,
                         state_assets=state_assets,
                         national_assets=national_assets,
                         active_assets=active_assets,
                         maintenance_assets=maintenance_assets,
                         damaged_assets=damaged_assets,
                         lost_assets=lost_assets,
                         recent_transfers=recent_transfers,
                         recent_maintenance=recent_maintenance,
                         category_stats=category_stats)

# ==========
# Authentication Routes
# ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with security improvements"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        # Verificar existencia y estado del usuario
        if not user:
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Su cuenta está desactivada. Contacte al administrador del sistema.', 'warning')
            audit_log(None, 'LOGIN_BLOCKED', 'User', user.id, 
                     f'Intento de login en cuenta desactivada: {username}')
            return render_template('login.html')

        # Verificar contraseña
        if user.check_password(password):
            login_user(user, remember=remember)
            audit_log(user.id, 'LOGIN', 'User', user.id, 
                     f'Usuario {username} inició sesión desde IP {request.remote_addr}')

            # Mensaje según rol
            if user.is_superuser():
                flash(f'Bienvenido Superuser {user.full_name}. Tiene CONTROL TOTAL del sistema.', 'success')
            elif user.is_admin():
                flash(f'Bienvenido Administrador {user.full_name}.', 'success')
            else:
                flash(f'Bienvenido {user.full_name}.', 'info')

            return redirect(url_for('dashboard'))
        else:
            # Registrar intento fallido
            audit_log(None, 'LOGIN_FAILED', 'User', user.id, 
                     f'Intento fallido de login para usuario {username} desde IP {request.remote_addr}')
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    user_id = current_user.id
    logout_user()
    audit_log(user_id, 'LOGOUT', 'User', user_id, f'Usuario {username} cerró sesión')
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

# ==========
# User Management Routes (SUPERUSER ONLY)
# ==========

@app.route('/users')
@superuser_required
def list_users():
    """List all users - SOLO SUPERUSER"""
    users = User.query.all()
    return render_template('users/list.html', users=users)

@app.route('/user/new', methods=['GET', 'POST'])
@superuser_required
def new_user():
    """Create new user - SOLO SUPERUSER"""
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')

            # Verificar duplicados
            if User.query.filter_by(username=username).first():
                flash('El nombre de usuario ya existe.', 'danger')
                return redirect(url_for('new_user'))
            if User.query.filter_by(email=email).first():
                flash('El correo electrónico ya está registrado.', 'danger')
                return redirect(url_for('new_user'))

            password = request.form.get('password')
            if len(password) < 8:
                flash('La contraseña debe tener al menos 8 caracteres.', 'warning')
                return redirect(url_for('new_user'))

            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='scrypt'),
                full_name=request.form.get('full_name'),
                role=request.form.get('role', 'user'),
                is_active=True
            )

            db.session.add(user)
            db.session.commit()

            audit_log(current_user.id, 'CREATE_USER', 'User', user.id, 
                     f'Usuario {username} creado con rol {user.role}')
            flash(f'Usuario {username} creado exitosamente.', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    return render_template('users/form.html', user=None)

@app.route('/user/<int:user_id>/toggle', methods=['POST'])
@superuser_required
def toggle_user(user_id):
    """Activate/Deactivate user - SOLO SUPERUSER"""
    user = User.query.get_or_404(user_id)

    # No permitir desactivar al superuser principal
    if user.username == 'admin' and user.is_superuser():
        flash('No puede desactivar al superuser principal del sistema.', 'danger')
        return redirect(url_for('list_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activado' if user.is_active else 'desactivado'
    audit_log(current_user.id, 'TOGGLE_USER', 'User', user.id, 
             f'Usuario {user.username} {status}')
    flash(f'Usuario {user.username} {status}.', 'success')
    return redirect(url_for('list_users'))

@app.route('/user/<int:user_id>/delete', methods=['POST'])
@superuser_required
def delete_user(user_id):
    """Delete user - SOLO SUPERUSER"""
    user = User.query.get_or_404(user_id)

    # Proteger al superuser principal
    if user.username == 'admin':
        flash('No puede eliminar al superuser principal del sistema.', 'danger')
        return redirect(url_for('list_users'))

    # No permitir auto-eliminación
    if user.id == current_user.id:
        flash('No puede eliminar su propia cuenta.', 'danger')
        return redirect(url_for('list_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    audit_log(current_user.id, 'DELETE_USER', 'User', user_id, 
             f'Usuario {username} eliminado del sistema')
    flash(f'Usuario {username} eliminado.', 'success')
    return redirect(url_for('list_users'))

# ==========
# Asset Routes
# ==========

@app.route('/assets')
@login_required
def list_assets():
    """List all assets"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Filters
    asset_type = request.args.get('asset_type', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    location = request.args.get('location', '')
    search = request.args.get('search', '')

    query = Asset.query

    if asset_type:
        query = query.filter_by(asset_type=asset_type)
    if category:
        query = query.filter_by(category_id=category)
    if status:
        query = query.filter_by(status=status)
    if location:
        query = query.filter_by(location_id=location)
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            (Asset.barcode.like(search_term)) |
            (Asset.serial_number.like(search_term)) |
            (Asset.name.like(search_term))
        )

    query = query.order_by(Asset.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()

    return render_template('assets/list.html',
                         assets=pagination.items,
                         pagination=pagination,
                         categories=categories,
                         locations=locations,
                         asset_type=asset_type,
                         category=category,
                         status=status,
                         location=location,
                         search=search)

@app.route('/asset/new', methods=['GET', 'POST'])
@login_required
def new_asset():
    """Create new asset"""
    if request.method == 'POST':
        try:
            barcode = request.form.get('barcode')

            # Check if barcode already exists
            if Asset.query.filter_by(barcode=barcode).first():
                flash('El código de barras ya existe.', 'danger')
                return redirect(url_for('new_asset'))

            asset = Asset(
                asset_type=request.form.get('asset_type'),
                barcode=barcode,
                serial_number=request.form.get('serial_number', ''),
                rfid_tag=request.form.get('rfid_tag', ''),
                name=request.form.get('name'),
                description=request.form.get('description', ''),
                model=request.form.get('model', ''),
                category_id=int(request.form.get('category_id')),
                brand_id=int(request.form.get('brand_id')) if request.form.get('brand_id') else None,
                location_id=int(request.form.get('location_id')),
                assigned_to=request.form.get('assigned_to', ''),
                status=request.form.get('status', Config.STATUS_ACTIVE),
                condition=request.form.get('condition', ''),
                is_operational='is_operational' in request.form,
                registered_by=current_user.id,
                updated_by=current_user.id
            )

            # Dates
            if request.form.get('acquisition_date'):
                asset.acquisition_date = datetime.strptime(request.form.get('acquisition_date'), '%Y-%m-%d')
            if request.form.get('warranty_expiry'):
                asset.warranty_expiry = datetime.strptime(request.form.get('warranty_expiry'), '%Y-%m-%d')

            # Price
            if request.form.get('purchase_price'):
                asset.purchase_price = request.form.get('purchase_price')

            asset.invoice_number = request.form.get('invoice_number', '')

            # Specifications
            specs = {}
            for key, value in request.form.items():
                if key.startswith('spec_'):
                    field_name = key.replace('spec_', '')
                    specs[field_name] = value
            asset.specifications = specs if specs else None

            db.session.add(asset)
            db.session.commit()

            audit_log(current_user.id, 'CREATE', 'Asset', asset.id, f'Asset {barcode} creado')

            flash('Activo registrado correctamente.', 'success')
            return redirect(url_for('list_assets'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el activo: {str(e)}', 'danger')

    categories = Category.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    brands = Brand.query.filter_by(is_active=True).all()

    return render_template('assets/form.html',
                         categories=categories,
                         locations=locations,
                         brands=brands,
                         asset=None)

@app.route('/asset/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    """View asset details"""
    asset = Asset.query.get_or_404(asset_id)
    maintenance = MaintenanceRecord.query.filter_by(asset_id=asset_id).order_by(MaintenanceRecord.date.desc()).all()
    transfers = AssetTransfer.query.filter_by(asset_id=asset_id).order_by(AssetTransfer.transfer_date.desc()).all()
    images = AssetImage.query.filter_by(asset_id=asset_id).all()

    return render_template('assets/detail.html',
                         asset=asset,
                         maintenance=maintenance,
                         transfers=transfers,
                         images=images)

@app.route('/asset/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    """Edit asset"""
    asset = Asset.query.get_or_404(asset_id)

    if request.method == 'POST':
        try:
            # Check if barcode changed
            new_barcode = request.form.get('barcode')
            if new_barcode != asset.barcode:
                if Asset.query.filter(Asset.barcode == new_barcode, Asset.id != asset_id).first():
                    flash('El código de barras ya existe.', 'danger')
                    return redirect(url_for('edit_asset', asset_id=asset_id))

            asset.barcode = new_barcode
            asset.serial_number = request.form.get('serial_number', '')
            asset.rfid_tag = request.form.get('rfid_tag', '')
            asset.name = request.form.get('name')
            asset.description = request.form.get('description', '')
            asset.model = request.form.get('model', '')
            asset.category_id = int(request.form.get('category_id'))
            asset.brand_id = int(request.form.get('brand_id')) if request.form.get('brand_id') else None
            asset.location_id = int(request.form.get('location_id'))
            asset.assigned_to = request.form.get('assigned_to', '')
            asset.status = request.form.get('status')
            asset.condition = request.form.get('condition', '')
            asset.is_operational = 'is_operational' in request.form
            asset.updated_by = current_user.id

            # Dates
            if request.form.get('acquisition_date'):
                asset.acquisition_date = datetime.strptime(request.form.get('acquisition_date'), '%Y-%m-%d')
            else:
                asset.acquisition_date = None

            if request.form.get('warranty_expiry'):
                asset.warranty_expiry = datetime.strptime(request.form.get('warranty_expiry'), '%Y-%m-%d')
            else:
                asset.warranty_expiry = None

            # Price
            if request.form.get('purchase_price'):
                asset.purchase_price = request.form.get('purchase_price')
            else:
                asset.purchase_price = None

            asset.invoice_number = request.form.get('invoice_number', '')

            # Specifications
            specs = {}
            for key, value in request.form.items():
                if key.startswith('spec_'):
                    field_name = key.replace('spec_', '')
                    specs[field_name] = value
            asset.specifications = specs if specs else None

            db.session.commit()

            audit_log(current_user.id, 'UPDATE', 'Asset', asset.id, f'Asset {asset.barcode} actualizado')

            flash('Activo actualizado correctamente.', 'success')
            return redirect(url_for('asset_detail', asset_id=asset.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el activo: {str(e)}', 'danger')

    categories = Category.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    brands = Brand.query.filter_by(is_active=True).all()

    return render_template('assets/form.html',
                         asset=asset,
                         categories=categories,
                         locations=locations,
                         brands=brands)

@app.route('/asset/<int:asset_id>/delete', methods=['POST'])
@admin_required  # ← CORREGIDO: Usa el decorator admin_required
def delete_asset(asset_id):
    """Delete asset - REQUIERE ADMIN O SUPERUSER"""
    asset = Asset.query.get_or_404(asset_id)
    barcode = asset.barcode

    try:
        db.session.delete(asset)
        db.session.commit()

        audit_log(current_user.id, 'DELETE', 'Asset', asset_id, f'Asset {barcode} eliminado')

        flash('Activo eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el activo: {str(e)}', 'danger')

    return redirect(url_for('list_assets'))

# ==========
# Asset Transfer Routes
# ==========

@app.route('/asset/<int:asset_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer_asset(asset_id):
    """Transfer asset to different location"""
    asset = Asset.query.get_or_404(asset_id)

    if request.method == 'POST':
        try:
            transfer = AssetTransfer(
                asset_id=asset_id,
                from_location_id=asset.location_id,
                to_location_id=int(request.form.get('to_location_id')),
                transferred_by=current_user.full_name,
                reason=request.form.get('reason', ''),
                transfer_date=datetime.strptime(request.form.get('transfer_date'), '%Y-%m-%d') if request.form.get('transfer_date') else datetime.now().date(),
                authorized_by=request.form.get('authorized_by', '')
            )

            # Update asset location
            asset.location_id = transfer.to_location_id
            asset.updated_by = current_user.id

            db.session.add(transfer)
            db.session.add(asset)
            db.session.commit()

            audit_log(current_user.id, 'TRANSFER', 'Asset', asset_id, 
                     f'Asset {asset.barcode} transferido de ubicación {transfer.from_location_id} a {transfer.to_location_id}')

            flash('Activo trasladado correctamente.', 'success')
            return redirect(url_for('asset_detail', asset_id=asset_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al trasladar el activo: {str(e)}', 'danger')

    locations = Location.query.filter(Location.id != asset.location_id, Location.is_active == True).all()

    return render_template('assets/transfer.html', asset=asset, locations=locations)

# ==========
# Maintenance Routes
# ==========

@app.route('/asset/<int:asset_id>/maintenance/new', methods=['GET', 'POST'])
@login_required
def new_maintenance(asset_id):
    """Add maintenance record"""
    asset = Asset.query.get_or_404(asset_id)

    if request.method == 'POST':
        try:
            maintenance = MaintenanceRecord(
                asset_id=asset_id,
                type=request.form.get('type'),
                title=request.form.get('title'),
                description=request.form.get('description', ''),
                performed_by=request.form.get('performed_by', ''),
                cost=request.form.get('cost') if request.form.get('cost') else None,
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d') if request.form.get('date') else datetime.now().date(),
                next_maintenance=datetime.strptime(request.form.get('next_maintenance'), '%Y-%m-%d') if request.form.get('next_maintenance') else None,
                status=request.form.get('status', 'COMPLETED')
            )

            # Update asset status if maintenance
            if request.form.get('type') == 'CORRECTIVE':
                asset.status = Config.STATUS_MAINTENANCE

            db.session.add(maintenance)
            db.session.add(asset)
            db.session.commit()

            audit_log(current_user.id, 'MAINTENANCE', 'MaintenanceRecord', maintenance.id, 
                     f'Mantenimiento registrado para asset {asset.barcode}')

            flash('Registro de mantenimiento creado.', 'success')
            return redirect(url_for('asset_detail', asset_id=asset_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar mantenimiento: {str(e)}', 'danger')

    return render_template('maintenance/form.html', asset=asset)

# ==========
# Reports Routes
# ==========

@app.route('/reports')
@login_required
def reports():
    """Reports dashboard"""
    return render_template('reports/index.html')

@app.route('/reports/assets-by-category')
@login_required
def report_assets_by_category():
    """Assets by category report"""
    categories = Category.query.filter_by(is_active=True).all()
    data = []

    for cat in categories:
        count = Asset.query.filter_by(category_id=cat.id).count()
        if count > 0:
            state_count = Asset.query.filter_by(category_id=cat.id, asset_type=Config.STATE_ASSET).count()
            national_count = Asset.query.filter_by(category_id=cat.id, asset_type=Config.NATIONAL_ASSET).count()
            data.append({
                'category': cat.name,
                'total': count,
                'state': state_count,
                'national': national_count
            })

    return render_template('reports/assets_by_category.html', data=data)

@app.route('/reports/assets-by-status')
@login_required
def report_assets_by_status():
    """Assets by status report"""
    data = []
    for status in Config.get_statuses():
        count = Asset.query.filter_by(status=status).count()
        if count > 0:
            data.append({'status': status, 'count': count})

    return render_template('reports/assets_by_status.html', data=data)

@app.route('/reports/assets-by-location')
@login_required
def report_assets_by_location():
    """Assets by location report"""
    locations = Location.query.filter_by(is_active=True).all()
    data = []

    for loc in locations:
        count = Asset.query.filter_by(location_id=loc.id).count()
        if count > 0:
            data.append({
                'location': loc.name,
                'type': loc.type,
                'count': count
            })

    return render_template('reports/assets_by_location.html', data=data)

@app.route('/reports/warranty-expiring')
@login_required
def report_warranty_expiring():
    """Assets with warranty expiring within 6 months"""
    six_months = datetime.now().date() + timedelta(days=180)

    assets = Asset.query.filter(
        Asset.warranty_expiry.isnot(None),
        Asset.warranty_expiry <= six_months,
        Asset.warranty_expiry >= datetime.now().date()
    ).order_by(Asset.warranty_expiry).all()

    return render_template('reports/warranty_expiring.html', assets=assets)

@app.route('/reports/maintenance-summary')
@login_required
def report_maintenance_summary():
    """Maintenance summary report"""
    maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).limit(100).all()

    # Summary by type
    preventive = MaintenanceRecord.query.filter_by(type='PREVENTIVE').count()
    corrective = MaintenanceRecord.query.filter_by(type='CORRECTIVE').count()
    inspection = MaintenanceRecord.query.filter_by(type='INSPECTION').count()

    total_cost = db.session.query(db.func.sum(MaintenanceRecord.cost)).filter(MaintenanceRecord.cost.isnot(None)).scalar() or 0

    return render_template('reports/maintenance_summary.html',
                         records=maintenance_records,
                         preventive=preventive,
                         corrective=corrective,
                         inspection=inspection,
                         total_cost=total_cost)

# ==========
# API Routes
# ==========

@app.route('/api/assets')
@login_required
def api_assets():
    """API endpoint for assets"""
    assets = Asset.query.all()
    return jsonify([{
        'id': a.id,
        'barcode': a.barcode,
        'name': a.name,
        'serial_number': a.serial_number,
        'category': a.category.name if a.category else None,
        'location': a.location.name if a.location else None,
        'status': a.status,
        'asset_type': a.asset_type
    } for a in assets])

@app.route('/api/audit-log')
@admin_required  # ← CORREGIDO: Solo admin/superuser puede ver logs
def api_audit_log():
    """API endpoint for audit log"""
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return jsonify([{
        'id': log.id,
        'user': log.user.full_name if log.user else 'Unknown',
        'action': log.action,
        'entity_type': log.entity_type,
        'entity_id': log.entity_id,
        'description': log.description,
        'created_at': log.created_at.strftime(Config.DATETIME_FORMAT) if log.created_at else ''
    } for log in logs])

# ==========
# Helper Functions
# ==========

def audit_log(user_id, action, entity_type, entity_id, description):
    """Create audit log entry"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=request.remote_addr if request else ''
    )
    db.session.add(log)
    db.session.commit()

# ==========
# CLI Setup
# ==========

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database"""
    init_db(app)

@app.cli.command('create-admin')
def create_admin():
    """Create admin user with FULL CONTROL"""
    import click
    username = click.prompt('Username', default='admin')
    email = click.prompt('Email', default='admin@corp-salud-tachira.gob.ve')
    full_name = click.prompt('Full Name', default='Administrador del Sistema')
    password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

    # Validación de contraseña
    if len(password) < 8:
        print('Error: La contraseña debe tener al menos 8 caracteres.')
        return

    if User.query.filter_by(username=username).first():
        print('El usuario ya existe!')
        return

    # Determinar rol según si ya existe un superuser
    existing_superuser = User.query.filter_by(role='superuser').first()
    if existing_superuser:
        role = 'admin'
        print('Ya existe un superuser. Creando usuario admin.')
    else:
        role = 'superuser'
        print('Creando superuser con CONTROL TOTAL del sistema.')

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password, method='scrypt'),
        full_name=full_name,
        department='SOPORTE TÉCNICO',
        role=role,
        is_active=True
    )

    db.session.add(user)
    db.session.commit()
    print(f'Usuario {role} creado exitosamente!')

@app.cli.command('reset-db')
def reset_db():
    """Reset database"""
    import click
    if click.confirm('¿Está seguro de que desea reiniciar la base de datos? Todos los datos se perderán.'):
        db.drop_all()
        db.create_all()
        print('Base de datos reiniciada exitosamente!')

@app.cli.command('list-users')
def list_users_cli():
    """List all users with roles"""
    users = User.query.all()
    print("\n" + "="*60)
    print("USUARIOS DEL SISTEMA - CORPOSALUD TÁCHIRA")
    print("="*60)
    for u in users:
        status = "ACTIVO" if u.is_active else "INACTIVO"
        print(f"ID: {u.id} | Usuario: {u.username} | Rol: {u.role.upper()} | Estado: {status} | Nombre: {u.full_name}")
    print("="*60 + "\n")

@app.cli.command('promote-user')
def promote_user():
    """Promote user to superuser"""
    import click
    username = click.prompt('Username del usuario a promover')
    user = User.query.filter_by(username=username).first()

    if not user:
        print('Usuario no encontrado.')
        return

    print(f'Usuario actual: {user.username} | Rol actual: {user.role}')
    new_role = click.prompt('Nuevo rol (user/admin/superuser)', default='superuser')

    if new_role not in ['user', 'admin', 'superuser']:
        print('Rol inválido.')
        return

    user.role = new_role
    db.session.commit()
    print(f'Usuario {username} promovido a {new_role} exitosamente!')

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
