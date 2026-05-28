import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Config:
    """Configuration for the Asset Inventory System"""
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'corp-salud-tachira-2026-secret-key'
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or 'sqlite:///inventory.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    UPLOAD_FOLDER: str = 'static/uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    
    # Asset types
    STATE_ASSET: str = 'ESTADAL'
    NATIONAL_ASSET: str = 'NACIONAL'
    
    # Asset statuses
    STATUS_ACTIVE: str = 'ACTIVO'
    STATUS_INACTIVE: str = 'INACTIVO'
    STATUS_MAINTENANCE: str = 'EN MANTENIMIENTO'
    STATUS_DAMAGED: str = 'DAÑADO'
    STATUS_LOST: str = 'EXTRAVIADO'
    
    # Date format
    DATE_FORMAT: str = '%d/%m/%Y'
    DATETIME_FORMAT: str = '%d/%m/%Y %H:%M:%S'
    
    @staticmethod
    def get_asset_types():
        return [Config.STATE_ASSET, Config.NATIONAL_ASSET]
    
    @staticmethod
    def get_statuses():
        return [
            Config.STATUS_ACTIVE,
            Config.STATUS_INACTIVE,
            Config.STATUS_MAINTENANCE,
            Config.STATUS_DAMAGED,
            Config.STATUS_LOST
        ]
    
    @staticmethod
    def get_departments():
        return [
            'SOPORTE TÉCNICO',
            'RECURSOS HUMANOS',
            'FINANZAS',
            'COMPRAS',
            'ALMACÉN',
            'INFORMÁTICA',
            'MANTENIMIENTO'
        ]