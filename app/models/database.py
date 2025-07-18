"""
Gerenciador de banco de dados com pool de conexões MongoDB.
"""
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador singleton para conexões MongoDB."""
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[MongoClient] = None
    _database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config):
        """Inicializa a conexão com o banco de dados."""
        if self._client is None:
            try:
                mongo_uri = config.get('MONGO_URI', 'mongodb://localhost:27017/attenua')
                max_pool = config.get('MONGO_MAX_POOL_SIZE', 10)
                min_pool = config.get('MONGO_MIN_POOL_SIZE', 1)
                
                self._client = MongoClient(
                    mongo_uri,
                    maxPoolSize=max_pool,
                    minPoolSize=min_pool,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    w='majority'
                )
                
                # Testa a conexão
                self._client.admin.command('ping')
                
                # Extrai nome do banco da URI
                db_name = mongo_uri.split('/')[-1].split('?')[0]
                if not db_name or db_name == '':
                    db_name = 'attenua'
                
                self._database = self._client[db_name]
                
                # Cria índices otimizados
                self._create_indexes()
                
                logger.info(f"Conectado ao MongoDB: {db_name}")
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Erro ao conectar ao MongoDB: {e}")
                # Em desenvolvimento, usar dados em memória
                self._database = None
    
    def _create_indexes(self):
        """Cria índices otimizados para performance."""
        try:
            # Índice para busca de cabines por ID
            self._database.cabines.create_index("id", unique=True)
            
            # Índice composto para consultas de disponibilidade
            self._database.cabines.create_index([
                ("agendamentos.dia", 1),
                ("agendamentos.hora", 1)
            ])
            
            # Índice para busca por código único
            self._database.cabines.create_index("agendamentos.senha_unica")
            
            logger.info("Índices criados com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao criar índices: {e}")
    
    @property
    def database(self):
        """Retorna a instância do banco de dados."""
        return self._database
    
    @property
    def cabines(self):
        """Retorna a coleção de cabines."""
        if self._database:
            return self._database.cabines
        return None
    
    def close(self):
        """Fecha a conexão com o banco."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Conexão MongoDB fechada")
    
    def health_check(self) -> bool:
        """Verifica se a conexão está saudável."""
        try:
            if self._client:
                self._client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
        return False

# Instância global do gerenciador
db_manager = DatabaseManager()

