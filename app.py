"""
Aplicação principal Attenua v2.0
Sistema de reservas de cabines com arquitetura modular e performance otimizada.
"""
import os
import logging
from flask import Flask
from flask_caching import Cache
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='development'):
    """Factory function para criar a aplicação Flask."""
    
    app = Flask(__name__)
    
    # === CONFIGURAÇÕES ===
    from app.config import Config
    app.config.from_object(Config)
    
    # === INICIALIZAÇÃO DE SERVIÇOS ===
    
    # Cache
    from app.utils import cache
    cache.init_app(app)
    
    # Database
    from app.models import db_manager
    db_manager.initialize(app.config)
    
    # Email Service
    from app.utils import email_service
    email_service.initialize(app.config)
    
    # MQTT Service
    from app.utils import mqtt_service
    mqtt_service.initialize(app.config)
    
    # === BLUEPRINTS ===
    from app.views import main_bp, api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # === MIDDLEWARE E HOOKS ===
    
    _first_request_done = False
    
    @app.before_request
    def before_first_request():
        """Executado antes da primeira requisição."""
        nonlocal _first_request_done
        if not _first_request_done:
            logger.info("Attenua v2.0 iniciando...")
            
            # Warm-up do cache
            from app.utils import warm_up_cache
            warm_up_cache()
            
            logger.info("Aplicação pronta para receber requisições")
            _first_request_done = True
    
    @app.before_request
    def before_request():
        """Executado antes de cada requisição."""
        # Adiciona timestamp para métricas de performance
        from flask import g
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Executado após cada requisição."""
        from flask import g, request
        
        # Calcula tempo de resposta
        if hasattr(g, 'start_time'):
            response_time = (time.time() - g.start_time) * 1000
            response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
        
        # Headers de segurança básicos
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache headers para assets estáticos
        if request.endpoint == 'static':
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 ano
        
        return response
    
    @app.teardown_appcontext
    def teardown_appcontext(error):
        """Limpeza após cada requisição."""
        if error:
            logger.error(f"Erro na requisição: {error}")
    
    # === HANDLERS DE ERRO GLOBAIS ===
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handler global para 404."""
        from flask import render_template
        return render_template('error.html', 
                             message="Página não encontrada",
                             code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handler global para 500."""
        from flask import render_template
        logger.error(f"Erro interno: {error}")
        return render_template('error.html',
                             message="Erro interno do servidor",
                             code=500), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handler para exceções não tratadas."""
        logger.error(f"Exceção não tratada: {error}", exc_info=True)
        from flask import render_template
        return render_template('error.html',
                             message="Erro inesperado",
                             code=500), 500
    
    # === COMANDOS CLI ===
    
    @app.cli.command()
    def init_db():
        """Inicializa o banco de dados com dados padrão."""
        from app.models import cabin_service
        
        logger.info("Inicializando banco de dados...")
        
        # Força inicialização das cabines padrão
        cabins = cabin_service.get_all_cabins()
        logger.info(f"Banco inicializado com {len(cabins)} cabines")
    
    @app.cli.command()
    def clear_cache():
        """Limpa todo o cache da aplicação."""
        from app.utils import cache_stats
        
        logger.info("Limpando cache...")
        success = cache_stats.clear_all()
        
        if success:
            logger.info("Cache limpo com sucesso")
        else:
            logger.error("Erro ao limpar cache")
    
    @app.cli.command()
    def test_services():
        """Testa conectividade dos serviços externos."""
        logger.info("Testando serviços...")
        
        # Teste MongoDB
        db_healthy = db_manager.health_check()
        logger.info(f"MongoDB: {'✓' if db_healthy else '✗'}")
        
        # Teste MQTT
        mqtt_status = mqtt_service.get_status()
        logger.info(f"MQTT: {'✓' if mqtt_status['connected'] else '✗'}")
        
        # Teste Email
        email_healthy = email_service.test_connection()
        logger.info(f"Email: {'✓' if email_healthy else '✗'}")
    
    # === CONTEXT PROCESSORS ===
    
    @app.context_processor
    def inject_globals():
        """Injeta variáveis globais nos templates."""
        return {
            'app_version': '2.0',
            'current_year': time.strftime('%Y')
        }
    
    # === SHUTDOWN HANDLER ===
    
    def shutdown_handler():
        """Limpeza ao encerrar a aplicação."""
        logger.info("Encerrando Attenua v2.0...")
        
        try:
            # Fecha conexões
            db_manager.close()
            email_service.close()
            mqtt_service.close()
            
            logger.info("Aplicação encerrada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao encerrar aplicação: {e}")
    
    import atexit
    atexit.register(shutdown_handler)
    
    return app

# === PONTO DE ENTRADA ===
if __name__ == '__main__':
    app = create_app()
    
    # Configurações para desenvolvimento
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )

