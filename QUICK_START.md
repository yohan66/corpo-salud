# 🚀 INICIO RÁPIDO
## Sistema de Inventario - CORPOSALUD Táchira

### 1. Iniciar el Sistema
```bash
cd /Users/yohan/Desktop/Codigo Python Johan/CORPO SALUD
flask --app app run --port=5000
```

Acceder: http://localhost:5000

### 2. Credenciales por Defecto
- Usuario: `admin`
- Contraseña: `Admin2024!`

### 3. Comandos Útiles

```bash
# Reiniciar base de datos
flask --app app reset-db

# Regenerar datos demo
flask --app app setup
flask --app app generate-demo-data

# CLI - Listar activos
python manage.py list

# CLI - Buscar activo
python manage.py find INV-2026-0001

# CLI - Estadísticas
python manage.py stats
```

### 4. Funcionalidades Principales

#### 📦 Inventario
- **Ruta**: Menu → Inventario
- Registrar nuevos activos
- Buscar por código/serie
- Filtrar por tipo, estado, ubicación

#### 🔄 Transferencias
- **Ruta**: Detalle del activo → Transferir
- Mover entre ubicaciones
- Registrar responsable
- Historial completo

#### 🔧 Mantenimiento
- **Ruta**: Detalle del activo → Mantenimiento
- Preventivo, Correctivo, Inspección
- Control de costos
- Próximo mantenimiento

#### 📊 Reportes
- **Ruta**: Menu → Reportes
- Por categoría, estado, ubicación
- Garantías por vencer
- Resumen de mantenimiento

### 5. Tipos de Usuario

| Rol | Permisos |
|-----|----------|
| **SuperAdmin** | Acceso total, eliminar usuarios |
| **Admin** | Gestión completa, sin eliminar |
| **User** | Consulta y registro básico |

### 6. Atajos Rápidos

| Acción | Método |
|--------|--------|
| Nuevo activo | + Nuevo Activo |
| Buscar | Barra superior |
| Transferir | Botón Transferir |
| Mantenimiento | Botón Mantenimiento |
| Exportar | Imprimir página |
| Ayuda | Documentación README.md |

### 7. Ejemplos de Código

**Registrar Activo:**
- Código: `INV-2026-0001`
- Tipo: ESTADAL / NACIONAL
- Categoría: Computadoras, Servidores, etc.
- Ubicación: Seleccionar de lista

**Transferir:**
- Seleccionar activo
- Nueva ubicación
- Fecha de transferencia
- Responsable
- Motivo

**Mantenimiento:**
- Tipo: Preventivo / Correctivo / Inspección
- Fecha
- Descripción
- Ejecutado por
- Costo

### 8. Seguridad

✅ Contraseñas hasheadas con scrypt  
✅ Sesiones protegidas  
✅ Registro de auditoría  
✅ Roles y permisos  
✅ Validación de datos  
✅ Prevención CSRF  

### 9. Soporte

📧 soporte@corp-salud-tachira.gob.ve  
📞 Departamento de Soporte Técnico  

### 10. Base de Datos

- **Archivo**: `instance/inventory.db`
- **Backup**: Copiar archivo periodicamente
- **Restaurar**: Reemplazar archivo
- **Ver datos**: SQLite Browser

---

💡 **Tip**: Usar códigos de barras físicos para inventario real