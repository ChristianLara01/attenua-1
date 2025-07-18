"""
Configurações centralizadas da aplicação Attenua v2.0
"""
import os
from datetime import timedelta

class Config:
    """Configuração base da aplicação."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/attenua')
    MONGO_MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '50'))
    MONGO_MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '5'))
    
    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Reservas
    INTERVAL_MIN = int(os.getenv('INTERVAL_MIN', '30'))
    HOUR_START = int(os.getenv('HOUR_START', '9'))
    HOUR_END = int(os.getenv('HOUR_END', '19'))
    
    # MQTT
    MQTT_HOST = os.getenv('MQTT_HOST', 'mqtt.eclipseprojects.io')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'estado')
    MQTT_TIMEOUT = int(os.getenv('MQTT_TIMEOUT', '10'))
    
    # SMTP
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.hostinger.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    SMTP_USER = os.getenv('SMTP_USER', 'christian@atualle.com.br')
    SMTP_PASS = os.getenv('SMTP_PASS', '@12Duda04')  # Manter por compatibilidade
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Assets
    MINIFY_HTML = True
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento."""
    DEBUG = True
    CACHE_TYPE = 'simple'

class ProductionConfig(Config):
    """Configuração para produção."""
    DEBUG = False
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class TestingConfig(Config):
    """Configuração para testes."""
    TESTING = True
    CACHE_TYPE = 'null'
    MONGO_URI = 'mongodb://localhost:27017/attenua_test'

# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

