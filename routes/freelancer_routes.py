import os
import logging
import math
import json
from datetime import datetime
from flask import request, jsonify, current_app
from scrapers.freelancer_scraper import FreelancerScraper

# Initialiser le logger pour ce module
logger = logging.getLogger(__name__)

# Initialiser le scraper
scraper = FreelancerScraper()

def get_mock_data():
    """Données mockées pour les tests"""
    return [
        {
            "title": "Développement d'une application mobile React Native",
            "description": "Nous recherchons un développeur expérimenté pour créer une application mobile cross-platform avec React Native. L'application doit inclure un système d'authentification, une interface utilisateur moderne et une intégration API REST.",
            "platform": "freelancer.ma",
            "url": "https://freelancer.ma/projet/dev-mobile-react-native-123",
            "budget": "15000 MAD",
            "date_posted": "Il y a 2 heures",
            "deadline": "Dans 15 jours"
        },
        {
            "title": "Création d'un site web e-commerce avec WordPress",
            "description": "Création d'un site e-commerce complet avec WordPress et WooCommerce. Le site doit avoir un design responsive, un système de paiement intégré et une gestion des stocks automatisée.",
            "platform": "freelancer.ma",
            "url": "https://freelancer.ma/projet/site-ecommerce-wordpress-456",
            "budget": "8000 MAD",
            "date_posted": "Il y a 5 heures",
            "deadline": "Dans 20 jours"
        },
        {
            "title": "Design graphique pour identité visuelle d'entreprise",
            "description": "Nous avons besoin d'un designer graphique pour créer notre identité visuelle complète : logo, charte graphique, cartes de visite, en-têtes de lettre et templates de présentation PowerPoint.",
            "platform": "freelancer.ma",
            "url": "https://freelancer.ma/projet/design-identite-visuelle-789",
            "budget": "5000 MAD",
            "date_posted": "Il y a 1 jour",
            "deadline": "Dans 10 jours"
        },
        {
            "title": "Développement d'une API REST avec Node.js",
            "description": "Création d'une API REST robuste avec Node.js et Express. L'API doit gérer l'authentification JWT, la validation des données, la documentation Swagger et les tests unitaires.",
            "platform": "freelancer.ma",
            "url": "https://freelancer.ma/projet/api-rest-nodejs-101",
            "budget": "12000 MAD",
            "date_posted": "Il y a 3 heures",
            "deadline": "Dans 25 jours"
        },
        {
            "title": "Rédaction de contenu SEO pour site web",
            "description": "Rédaction d'articles optimisés SEO pour un site web dans le domaine de la technologie. 20 articles de 800 mots minimum avec recherche de mots-clés et optimisation pour les moteurs de recherche.",
            "platform": "freelancer.ma",
            "url": "https://freelancer.ma/projet/redaction-seo-tech-202",
            "budget": "3000 MAD",
            "date_posted": "Il y a 6 heures",
            "deadline": "Dans 30 jours"
        }
    ]

def register_routes(app):
    """Enregistre toutes les routes dans l'application Flask"""
    
    @app.before_request
    def log_request_info():
        """Log les informations de chaque requête"""
        logger.info(f"📥 Requête reçue: {request.method} {request.url}")
        logger.info(f"   - IP: {request.remote_addr}")
        logger.info(f"   - User-Agent: {request.headers.get('User-Agent', 'Non spécifié')[:50]}...")
        
        if request.is_json and request.get_json():
            logger.info(f"   - Données JSON: {request.get_json()}")

    @app.after_request
    def log_response_info(response):
        """Log les informations de chaque réponse"""
        logger.info(f"📤 Réponse envoyée: {response.status_code}")
        logger.info(f"   - Taille: {response.content_length or 'Non spécifiée'} bytes")
        return response

    @app.route("/", methods=["GET"])
    def health_check():
        """Point de santé de l'API"""
        logger.info("🏥 Health check appelé")
        
        response_data = {
            "status": "healthy",
            "service": "Freelancer Scraper API",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "mode": "mock" if current_app.config.get('MOCK_MODE') else "production",
            "endpoints": {
                "health": "GET /",
                "scraping": "POST /tools/get_freelancer_offres"
            }
        }
        
        logger.info("✅ Health check réussi")
        return jsonify(response_data)

    @app.route("/tools/get_freelancer_offres", methods=["POST"])
    def get_freelancer_offres():
        """Endpoint principal pour récupérer les offres freelancer"""
        start_time = datetime.now()
        request_id = f"req_{int(start_time.timestamp())}"
        
        logger.info(f"🎯 [{request_id}] Début du traitement de la demande d'offres")
        
        try:
            # Récupération et validation des données
            data = request.get_json(force=True)
            count = int(data.get("count", 25))
            
            logger.info(f"📊 [{request_id}] Paramètres reçus:")
            logger.info(f"   - Count demandé: {count}")
            
            # Validation des paramètres
            if count <= 0 or count > 1000:
                logger.warning(f"⚠️ [{request_id}] Paramètre count invalide: {count}")
                return jsonify([]), 400  # retourne une liste vide en cas d'erreur

            # Mode Mock ou Production
            if current_app.config.get('MOCK_MODE'):
                logger.info(f"🎭 [{request_id}] Mode MOCK activé - Simulation des données")
                import time
                time.sleep(0.5)
                mock_data = get_mock_data()
                result = mock_data[:count]
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ [{request_id}] Données mockées retournées avec succès")
                logger.info(f"   - Projets retournés: {len(result)}")
                logger.info(f"   - Temps d'exécution: {execution_time:.2f}s")
                return jsonify(result)  # retourne directement la liste

            else:
                logger.info(f"🔥 [{request_id}] Mode PRODUCTION - Scraping réel des données")
                projects_per_page = int(os.getenv('PROJECTS_PER_PAGE', 10))
                max_pages = math.ceil(count / projects_per_page)
                logger.info(f"📄 [{request_id}] Configuration du scraping:")
                logger.info(f"   - Pages à scraper: {max_pages}")
                logger.info(f"   - Projets par page: {projects_per_page}")
                projets = scraper.scrape_all_projects(max_pages=max_pages)
                result = projets[:count]
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ [{request_id}] Scraping réel terminé avec succès")
                logger.info(f"   - Projets trouvés: {len(projets)}")
                logger.info(f"   - Projets retournés: {len(result)}")
                logger.info(f"   - Pages scrapées: {max_pages}")
                logger.info(f"   - Temps d'exécution: {execution_time:.2f}s")
                return jsonify(result)  # retourne directement la liste

        except ValueError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ [{request_id}] Erreur de validation: {str(e)}")
            return jsonify([]), 400  # retourne une liste vide en cas d'erreur
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"💥 [{request_id}] Erreur inattendue: {str(e)}")
            logger.error(f"   - Temps écoulé: {execution_time:.2f}s")
            return jsonify([]), 500  # retourne une liste vide en cas d'erreur

    @app.errorhandler(404)
    def not_found(error):
        """Gestionnaire d'erreur 404"""
        logger.warning(f"🔍 Route non trouvée: {request.url}")
        return jsonify({
            "success": False,
            "error": "Route non trouvée",
            "available_endpoints": ["/", "/tools/get_freelancer_offres"]
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Gestionnaire d'erreur 500"""
        logger.error(f"💥 Erreur interne du serveur: {str(error)}")
        return jsonify({
            "success": False,
            "error": "Erreur interne du serveur"
        }),