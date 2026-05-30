# 🏥 Sistema de Inventario de Bienes - CORPORACIÓN DE SALUD DEL ESTADO TÁCHIRA

## Departamento de Soporte Técnico

### Descripción
Sistema integral de gestión de inventario para el control y seguimiento de bienes estatales y nacionales del Departamento de Soporte Técnico de la Corporación de Salud del Estado Táchira.

### Características Principales
- 📦 Gestión completa de inventario de activos
- 🎫 Clasificación por tipo (Bienes Estadales/Nacionales)
- 🏷️ Código de barras y etiquetas RFID
- 📍 Control de ubicaciones y asignaciones
- 🔧 Registro de mantenimiento preventivo y correctivo
- 🔄 Historial de transferencias
- 📊 Reportes detallados y exportables
- 👥 Control de acceso por usuarios y roles
- 🔍 Búsqueda avanzada con filtros
- 📅 Alertas de garantía próxima a vencer

### Requisitos del Sistema
- Python 3.8+
- Flask 3.0.0
- SQLite3 (incluido en Python)
- Navegador web moderno

### Instalación

1. Clonar o descargar el proyecto:
```bash
cd /Users/yohan/Desktop/Codigo Python Johan/CORPO SALUD
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Inicializar la base de datos:
```bash
flask --app app init-db
```

4. Configurar el sistema (opcional, datos de prueba):
```bash
flask --app app setup
```

5. Generar datos de demostración (opcional):
```bash
flask --app app generate-demo-data
```

### Ejecución

**Modo Desarrollo:**
```bash
flask --app app run
```

Acceder a: http://localhost:5000

**Modo Producción:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Usuarios por Defecto

| Usuario | Contraseña | Rol | Departamento |
|---------|------------|-----|--------------|
| admin | Admin2024! | SuperAdmin | Soporte Técnico |

### Estructura del Proyecto

```
corp-salud-tachira/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración del sistema
├── models.py             # Modelos de base de datos
├── manage.py             # CLI y gestión
├── requirements.txt      # Dependencias
├── README.md            # Documentación
├── instance/
│   └── inventory.db      # Base de datos SQLite
├── templates/
│   ├── base.html         # Plantilla base
│   ├── auth/
│   │   └── login.html    # Login
│   ├── assets/
│   │   ├── list.html     # Listado de activos
│   │   ├── form.html     # Formulario CRUD
│   │   ├── detail.html   # Detalle del activo
│   │   └── transfer.html # Transferencia
│   ├── maintenance/
│   │   └── form.html     # Registro de mantenimiento
│   ├── reports/
│   │   ├── index.html    # Dashboard de reportes
│   │   ├── assets_by_*.html
│   │   └── maintenance_summary.html
│   └── dashboard.html    # Dashboard principal
└── static/
    ├── css/
    ├── js/
    └── uploads/
```

### Modelo de Datos

#### Entidades Principales:

1. **User** - Usuarios del sistema
   - Roles: user, admin, superuser
   - Departamentos asignados

2. **Asset** - Activos/Inventario
   - Tipos: ESTADAL, NACIONAL
   - Estados: ACTIVO, INACTIVO, EN MANTENIMIENTO, DAÑADO, EXTRAVIADO
   - Categorías múltiples
   - Especificaciones JSON

3. **Category** - Categorías de activos
   - Códigos únicos
   - Descripciones

4. **Location** - Ubicaciones/Jerarquía
   - Tipos: DEPARTMENT, OFFICE, ROOM, WAREHOUSE
   - Relaciones padre-hijo

5. **MaintenanceRecord** - Historial de mantenimiento
   - Tipos: PREVENTIVE, CORRECTIVE, INSPECTION
   - Costos y fechas

6. **AssetTransfer** - Transferencias
   - Historial de movimientos
   - Autorizaciones

7. **Brand** - Marcas/Proveedores
8. **Supplier** - Proveedores
9. **Purchase** - Órdenes de compra
10. **AssetImage** - Fotografías
11. **AuditLog** - Auditoría de cambios

### Rutas Principales

#### Autenticación
- `GET /login` - Iniciar sesión
- `GET /logout` - Cerrar sesión

#### Dashboard
- `GET /` - Redirección
- `GET /dashboard` - Panel principal

#### Gestión de Activos
- `GET /assets` - Listar activos (con filtros)
- `GET /asset/new` - Crear nuevo
- `GET /asset/<id>` - Ver detalle
- `GET /asset/<id>/edit` - Editar
- `GET /asset/<id>/transfer` - Transferir
- `POST /asset/<id>/delete` - Eliminar

#### Mantenimiento
- `GET /asset/<id>/maintenance/new` - Nuevo registro

#### Reportes
- `GET /reports` - Dashboard de reportes
- `GET /reports/assets-by-category` - Por categoría
- `GET /reports/assets-by-status` - Por estado
- `GET /reports/assets-by-location` - Por ubicación
- `GET /reports/warranty-expiring` - Garantía por vencer
- `GET /reports/maintenance-summary` - Resumen mantenimiento

#### API
- `GET /api/assets` - Lista de activos (JSON)
- `GET /api/audit-log` - Log de auditoría (JSON)

### CLI Commands

```bash
# Inicializar base de datos
flask --app app init-db

# Configuración completa
flask --app app setup

# Generar datos de prueba
flask --app app generate-demo-data

# Crear admin
flask --app app create-admin

# Resetear base de datos
flask --app app reset-db

# Modo CLI
python manage.py list      # Listar activos
python manage.py find <barcode>  # Buscar activo
python manage.py stats     # Estadísticas
```

### Funcionalidades Detalladas

#### 1. Gestión de Activos
- Registro completo de activos con códigos únicos
- Categorización flexible
- Tracking de ubicaciones y responsables
- Especificaciones técnicas (JSON)
- Control de garantías

#### 2. Mantenimiento
- Registro de mantenimientos preventivos
- Mantenimientos correctivos
- Historial completo por activo
- Alertas de próximo mantenimiento
- Control de costos

#### 3. Transferencias
- Movimiento entre ubicaciones
- Autorización requerida
- Historial completo
- Motivos documentados

#### 4. Reportes
- Por categoría, estado, ubicación
- Garantías próximas a vencer
- Resumen de mantenimiento
- Exportación a PDF (impresión)
- Estadísticas interactivas

#### 5. Seguridad
- Autenticación de usuarios
- Roles y permisos
- Auditoría completa
- Registro de IPs
- Hash de contraseñas (scrypt)

### Seguridad

- ✅ Contraseñas hasheadas con scrypt
- ✅ Protección CSRF
- ✅ Validación de formularios
- ✅ Control de sesiones
- ✅ Registro de auditoría
- ✅ Permisos por roles
- ✅ Protección de inyección SQL (SQLAlchemy)
- ✅ Sanitización de inputs

### Mejores Prácticas

1. **Nombres de códigos**: Usar convención `INV-AAAA-NNNN`
2. **Fotos**: Documentar activos con imágenes
3. **Garantías**: Registrar y monitorear fechas
4. **Mantenimiento**: Programar preventivos regularmente
5. **Transferencias**: Documentar autorizaciones
6. **Auditoría**: Revisar logs periódicamente

### Personalización

#### Agregar nueva categoría:
```python
cat = Category(name='Nueva Categoría', code='CAT-XXX', description='...')
db.session.add(cat)
db.session.commit()
```

#### Agregar nueva ubicación:
```python
loc = Location(name='Nueva Ubicación', type='OFFICE', code='LOC-XXX')
db.session.add(loc)
db.session.commit()
```

### Soporte y Mantenimiento

- Revisar logs de auditoría mensualmente
- Actualizar estado de garantías trimestralmente
- Realizar inventario físico anual
- Backup de base de datos semanal
- Mantenimiento preventivo programado

### Licencia

Sistema desarrollado para uso interno de la Corporación de Salud del Estado Táchira.

### Contacto

**Departamento de Soporte Técnico**
Corporación de Salud del Estado Táchira
Venezuela

### Versión

v1.0.0 - Mayo 2026
- Sistema inicial de inventario
- Gestión completa de activos
- Reportes y auditoría
- Control de mantenimiento

---

**Nota**: Este sistema cumple con los requerimientos del Departamento de Soporte Técnico para el control efectivo de bienes estatales y nacionales, garantizando trazabilidad, seguridad y eficiencia en la gestión de activos institucionales."# corpo-salud"  
