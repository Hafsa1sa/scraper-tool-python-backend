import os
import sys
import logging
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
load_dotenv()

def setup_logging():
    """Configure le système de logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Créer le dossier logs s'il n'existe pas
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configuration du format des logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configuration du logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Pour afficher aussi dans la console
        ]
    )
    
    return logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration de l'application
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['MOCK_MODE'] = os.getenv('MOCK_MODE', 'False').lower() == 'true'
    app.config['HOST'] = os.getenv('HOST', '0.0.0.0')
    app.config['PORT'] = int(os.getenv('PORT', 5005))
    
    # Importer et enregistrer les routes
    from routes.freelancer_routes import register_routes
    register_routes(app)
    
    return app

def main():
    """Point d'entrée principal de l'application"""
    # Initialiser le logger
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE DE L'APPLICATION SCRAPER_TOOL")
    logger.info("=" * 60)
    
    # Créer l'application
    app = create_app()
    
    # Afficher la configuration
    logger.info(f"📊 Configuration:")
    logger.info(f"   - Host: {app.config['HOST']}")
    logger.info(f"   - Port: {app.config['PORT']}")
    logger.info(f"   - Debug: {'✅ Activé' if app.config['DEBUG'] else '❌ Désactivé'}")
    logger.info(f"   - Mock Mode: {'✅ Activé' if app.config['MOCK_MODE'] else '❌ Désactivé'}")
    logger.info(f"   - Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    
    try:
        logger.info("🌐 Serveur Flask démarré avec succès!")
        logger.info(f"📡 Accessible sur: http://{app.config['HOST']}:{app.config['PORT']}")
        logger.info("=" * 60)
        
        # Démarrer le serveur
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage du serveur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()