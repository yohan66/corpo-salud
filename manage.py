import click
from app import app, db, init_db, User, Category, Location, Brand, Supplier, Asset, MaintenanceRecord, AssetTransfer, Config
from werkzeug.security import generate_password_hash
from datetime import datetime
import random
import string
import faker

@click.group()
def cli():
    """Asset Inventory CLI"""
    pass

@cli.command()
def setup():
    """Setup the complete system"""
    click.echo('Setting up the Asset Inventory System...')
    
    # Create tables
    with app.app_context():
        db.create_all()
    click.echo('(OK) Database tables created')
    
    # Create default categories
    with app.app_context():
        categories = [
            {'name': 'Computadoras', 'code': 'CAT-001', 'description': 'Equipos de computo personales y portatiles'},
            {'name': 'Servidores', 'code': 'CAT-002', 'description': 'Equipos servidores de red y datos'},
            {'name': 'Impresoras', 'code': 'CAT-003', 'description': 'Impresoras, escaneres y multifuncionales'},
            {'name': 'Redes', 'code': 'CAT-004', 'description': 'Routers, switches, cables y equipos de red'},
            {'name': 'Monitores', 'code': 'CAT-005', 'description': 'Pantallas y monitores de visualizacion'},
            {'name': 'Telefonia', 'code': 'CAT-006', 'description': 'Telefonos, centrales y equipos de comunicacion'},
            {'name': 'Software', 'code': 'CAT-007', 'description': 'Licencias y software instalado'},
            {'name': 'Muebles', 'code': 'CAT-008', 'description': 'Mobiliario de oficina y estaciones de trabajo'},
            {'name': 'Vehiculos', 'code': 'CAT-009', 'description': 'Vehiculos institucionales'},
            {'name': 'Equipo Medico', 'code': 'CAT-010', 'description': 'Equipos y dispositivos medicos'}
        ]
        
        for cat_data in categories:
            if not Category.query.filter_by(code=cat_data['code']).first():
                cat = Category(**cat_data)
                db.session.add(cat)
        db.session.commit()
    click.echo('(OK) Categories created')
    
    # Create locations hierarchy
    with app.app_context():
        locations_data = [
            {'name': 'Soporte Tecnico - Oficina Principal', 'type': 'DEPARTMENT', 'code': 'LOC-ST-001'},
            {'name': 'Sala de Servidores', 'type': 'ROOM', 'code': 'LOC-ST-002', 'parent_id': 1},
            {'name': 'Almacen de Soporte', 'type': 'WAREHOUSE', 'code': 'LOC-ST-003', 'parent_id': 1},
            {'name': 'Piso 1 - Estaciones de Trabajo', 'type': 'ROOM', 'code': 'LOC-FL1-001'},
            {'name': 'Piso 2 - Estaciones de Trabajo', 'type': 'ROOM', 'code': 'LOC-FL2-001'},
            {'name': 'Mesa de Entrada', 'type': 'OFFICE', 'code': 'LOC-RE-001'},
            {'name': 'Laboratorio', 'type': 'ROOM', 'code': 'LOC-LB-001'},
        ]
        # Map for parent lookup
        loc_map = {}
        for loc in Location.query.all():
            loc_map[loc.code] = loc
        
        for loc_data in locations_data:
            if not Location.query.filter_by(code=loc_data['code']).first():
                if 'parent_id' in loc_data:
                    parent = Location.query.filter_by(code=['LOC-ST-001', 'LOC-FL1-001', 'LOC-FL2-001'][0]).first()
                    loc_data['parent_id'] = parent.id if parent else None
                loc = Location(**loc_data)
                db.session.add(loc)
        db.session.commit()
    click.echo('(OK) Locations created')
    
    # Create default admin user
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
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
    click.echo('(OK) Admin user created')
    click.echo('  Username: admin')
    click.echo('  Password: Admin2024!')
    
    click.echo('\nSystem setup complete! Run the following commands:')
    click.echo('  flask --app app run  # Start the web server')
    click.echo('  flask --app app generate-demo-data  # Generate demo data')

@cli.command()
def generate_demo_data():
    """Generate demo data for testing"""
    fake = faker.Faker('es_ES')
    
    with app.app_context():
        categories = Category.query.all()
        locations = Location.query.all()
        
        if not categories:
            click.echo('Please run setup first!')
            return
        
        # Import needed models
        from config import Config
        asset_types = [Config.STATE_ASSET, Config.NATIONAL_ASSET]
        statuses = [Config.STATUS_ACTIVE, Config.STATUS_ACTIVE, Config.STATUS_ACTIVE, Config.STATUS_INACTIVE, Config.STATUS_MAINTENANCE]
        
        # Generate brands
        brands_data = ['Dell', 'HP', 'Lenovo', 'Apple', 'Samsung', 'Asus', 'Acer', 'Cisco', 'TP-Link', 'Epson', 'Canon', 'Sony']
        for brand_name in brands_data:
            b = Brand.query.filter_by(name=brand_name).first()
            if not b:
                b = Brand(name=brand_name, country='Estados Unidos')
                db.session.add(b)
        db.session.commit()
        brands = Brand.query.all()
        
        # Generate suppliers
        suppliers_data = ['TechCorp SRL', 'Insumos Medicos C.A.', 'Computadoras del Tachira', 'Suministros Hospitalarios', 'Redes y Sistemas']
        for sup_name in suppliers_data:
            s = Supplier.query.filter_by(name=sup_name).first()
            if not s:
                s = Supplier(
                    name=sup_name,
                    rif=f'J-{random.randint(1000000000, 9999999999)}',
                    address=fake.address(),
                    phone=fake.phone_number(),
                    contact_person=fake.name()
                )
                db.session.add(s)
        db.session.commit()
        suppliers = Supplier.query.all()
        
        # Generate assets
        for i in range(50):
            barcode = f'INV-{datetime.now().year}-{i+1:04d}'
            category = random.choice(categories)
            location = random.choice(locations)
            asset_type = random.choice(asset_types)
            
            if Asset.query.filter_by(barcode=barcode).first():
                continue
            
            rfid = f'RFID-{i+1:04d}-{random.randint(1000,9999)}' if random.random() > 0.5 else None
            
            spec = {
                'cpu': f'Intel i{random.randint(3,9)}{random.choice(["3","5","7","9"])}',
                'ram': f'{random.choice([4,8,16,32])} GB',
                'storage': f'{random.choice([256,512,1024,2048])} GB'
            }
            
            asset = Asset(
                asset_type=asset_type,
                barcode=barcode,
                serial_number=f'SN-{random.randint(10000,99999)}-{i+1}',
                rfid_tag=rfid,
                name=f'{category.name} {fake.company()}',
                description=fake.catch_phrase(),
                model=f'Model-{random.randint(100,999)}',
                category_id=category.id,
                brand_id=random.choice(brands).id,
                location_id=location.id,
                assigned_to=fake.name() if random.random() > 0.5 else location.name,
                status=random.choice(statuses),
                condition=random.choice(['NEW','GOOD','FAIR','POOR']),
                is_operational=random.choice([True,True,True,False]),
                registered_by=1,
                updated_by=1,
                acquisition_date=fake.date_between(start_date='-3y', end_date='today'),
                warranty_expiry=fake.date_between(start_date='today', end_date='+2y') if random.random() > 0.4 else None,
                purchase_price=random.randint(100,10000),
                invoice_number=f'INV-{fake.bothify("######")}',
                specifications=spec
            )
            db.session.add(asset)
        db.session.commit()
    click.echo('(OK) Generated 50 demo assets')
    
    # Generate maintenance records
    with app.app_context():
        assets = Asset.query.all()
        for asset in assets[:20]:
            for _ in range(random.randint(0,3)):
                mtype = random.choice(['PREVENTIVE','CORRECTIVE','INSPECTION'])
                rec = MaintenanceRecord(
                    asset_id=asset.id,
                    type=mtype,
                    title=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=200),
                    performed_by=fake.name(),
                    cost=random.randint(50,500),
                    date=fake.date_between(start_date='-1y', end_date='today'),
                    next_maintenance=fake.date_between(start_date='today', end_date='+6m') if mtype == 'PREVENTIVE' else None,
                    status='COMPLETED'
                )
                db.session.add(rec)
        db.session.commit()
    click.echo('(OK) Generated maintenance records')
    
    # Generate transfers
    with app.app_context():
        assets = Asset.query.all()
        locs = Location.query.all()
        for asset in assets[:10]:
            for _ in range(random.randint(0,2)):
                from_loc = random.choice(locs)
                to_loc = random.choice([l for l in locs if l.id != from_loc.id])
                tr = AssetTransfer(
                    asset_id=asset.id,
                    from_location_id=from_loc.id,
                    to_location_id=to_loc.id,
                    transferred_by=fake.name(),
                    reason=fake.sentence(),
                    transfer_date=fake.date_between(start_date='-2y', end_date='today'),
                    authorized_by=fake.name()
                )
                db.session.add(tr)
        db.session.commit()
    click.echo('(OK) Generated transfer records')
    
    with app.app_context():
        click.echo('\nDemo data generated!')
        click.echo(f'  Total assets: {Asset.query.count()}')
        click.echo(f'  Total locations: {Location.query.count()}')
        click.echo(f'  Total categories: {Category.query.count()}')

@cli.command()
def list():
    """List all assets"""
    with app.app_context():
        assets = Asset.query.all()
        click.echo(f'\nTotal Assets: {len(assets)}\n')
        click.echo(f'{"ID":<5} {"Barcode":<20} {"Name":<30} {"Type":<10} {"Status":<15} {"Location":<20}')
        click.echo('-' * 100)
        for asset in assets:
            click.echo(f'{asset.id:<5} {asset.barcode:<20} {asset.name[:28]:<30} {asset.asset_type:<10} {asset.status:<15} {asset.location.name[:18]:<20}')

@cli.command()
@click.argument('barcode')
def find(barcode):
    """Find asset by barcode"""
    with app.app_context():
        asset = Asset.query.filter_by(barcode=barcode).first()
        if asset:
            click.echo(f'\nAsset Details:')
            click.echo(f'  Barcode: {asset.barcode}')
            click.echo(f'  Name: {asset.name}')
            click.echo(f'  Type: {asset.asset_type}')
            click.echo(f'  Category: {asset.category.name if asset.category else "N/A"}')
            click.echo(f'  Status: {asset.status}')
            click.echo(f'  Location: {asset.location.name if asset.location else "N/A"}')
            click.echo(f'  Assigned To: {asset.assigned_to}')
            click.echo(f'  Acquisition Date: {asset.acquisition_date}')
            click.echo(f'  Warranty Expiry: {asset.warranty_expiry}')
        else:
            click.echo(f'Asset with barcode {barcode} not found')

@cli.command()
def stats():
    """Show inventory statistics"""
    with app.app_context():
        from config import Config
        total = Asset.query.count()
        state = Asset.query.filter_by(asset_type=Config.STATE_ASSET).count()
        national = Asset.query.filter_by(asset_type=Config.NATIONAL_ASSET).count()
        active = Asset.query.filter_by(status=Config.STATUS_ACTIVE).count()
        maintenance = Asset.query.filter_by(status=Config.STATUS_MAINTENANCE).count()
        
        click.echo(f'\nInventory Statistics:')
        click.echo(f'  Total Assets: {total}')
        click.echo(f'  State Assets: {state} ({state/total*100:.1f}%)')
        click.echo(f'  National Assets: {national} ({national/total*100:.1f}%)')
        click.echo(f'  Active: {active} ({active/total*100:.1f}%)')
        click.echo(f'  In Maintenance: {maintenance} ({maintenance/total*100:.1f}%)')

if __name__ == '__main__':
    cli()