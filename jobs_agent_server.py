#!/usr/bin/env python3
"""
Serveur MCP pour les outils de scraping freelancer.ma
"""

import json
import uuid
import time
from flask import Flask, request, Response, stream_with_context
import sys
import os
import logging

# Assurez-vous d'importer vos modules de scraping et de modèle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.freelancer_scraper import FreelancerScraper
from models.project import Project

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialisez votre scraper en dehors de l'endpoint si possible
# Cela évite de créer un nouvel objet à chaque requête
freelancer_scraper = FreelancerScraper()

@app.route('/mcp/sse', methods=['POST'])
@stream_with_context
def mcp_sse_endpoint():
    print('Connection received on /mcp/sse')

    try:
        data = request.json
        if not data:
            print("ERROR: Invalid JSON payload")
            # Utilisez Response pour retourner un code d'erreur HTTP
            return Response("Invalid JSON payload", status=400, mimetype='text/plain')

        # Tentative de récupération des appels d'outils, en gérant les noms "tool_call" et "tool_calls"
        tool_calls = data.get('tool_calls', None)
        if not tool_calls:
            # Si 'tool_calls' n'existe pas, essayons 'tool_call'
            tool_call = data.get('tool_call', None)
            if tool_call:
                # Si c'est un seul appel, on le met dans une liste pour uniformiser
                tool_calls = [tool_call]

        if not tool_calls:
            print("ERROR: Invalid payload: 'tool_call' or 'tool_calls' is missing")
            return Response("Invalid payload: 'tool_call' or 'tool_calls' is missing", status=400, mimetype='text/plain')

        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            tool_arguments = tool_call.get('arguments', {})
            # Utilisez le tool_call_id fourni par le client s'il existe
            tool_call_id = tool_call.get('tool_call_id', str(uuid.uuid4()))

            # Gérer la logique en fonction du nom de l'outil
            if tool_name == 'get_freelancer_projects':
                max_pages = tool_arguments.get('max_pages', 2)

                try:
                    scraped_projects = freelancer_scraper.scrape_all_projects(max_pages)

                    # --- DÉBUT DE LA MODIFICATION CRUCIALE ---
                    # L'objet à envoyer au client Java doit avoir une clé "projects"
                    # pour correspondre à votre FreelancerResponseDTO.
                    tool_output_payload = {
                        "projects": scraped_projects
                    }

                    # L'objet complet est sérialisé en JSON, puis envoyé comme contenu de l'événement.
                    response_payload = {
                        "event": "tool_output",
                        "tool_output": {
                            "call_id": tool_call_id,
                            "content": json.dumps(tool_output_payload)
                        }
                    }
                    # --- FIN DE LA MODIFICATION CRUCIALE ---
                    yield f"data: {json.dumps(response_payload)}\n\n"

                except Exception as e:
                    print(f"ERROR: Scraping failed with error: {e}")
                    error_payload = {
                        "event": "error",
                        "content": f"Scraping failed: {e}"
                    }
                    yield f"data: {json.dumps(error_payload)}\n\n"

            else:
                error_payload = {
                    "event": "error",
                    "content": f"Unknown tool: {tool_name}"
                }
                yield f"data: {json.dumps(error_payload)}\n\n"

    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        error_payload = {
            "event": "error",
            "content": f"Internal server error: {e}"
        }
        yield f"data: {json.dumps(error_payload)}\n\n"
    
    # Ajoutez un événement de fin de flux
    yield "data: [DONE]\n\n"

if __name__ == '__main__':
    logger.info("🚀 Démarrage du serveur MCP en mode SSE")
    app.run(port=8001, debug=True)
