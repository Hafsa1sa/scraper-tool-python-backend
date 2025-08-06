import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from models.project import Project
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class FreelancerScraper:
    def __init__(self):
        self.base_url = "https://freelancer.ma"
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration depuis les variables d'environnement
        self.max_retry_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', 10))
        self.user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Configuration de la session HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.logger.info("🚀 FreelancerScraper initialisé avec succès")
        self.logger.debug(f"   - Base URL: {self.base_url}")
        self.logger.debug(f"   - Timeout: {self.request_timeout}s")
        self.logger.debug(f"   - Max retry: {self.max_retry_attempts}")

    def scrape_all_projects(self, max_pages=None):
        """Scrape tous les projets avec gestion des erreurs et logs détaillés"""
        start_time = time.time()
        all_projects = []
        page = 1
        consecutive_errors = 0
        max_consecutive_errors = 3

        self.logger.info("=" * 50)
        self.logger.info(f"🎯 DÉBUT DU SCRAPING")
        self.logger.info(f"   - Pages maximum: {max_pages if max_pages else 'illimitées'}")
        self.logger.info("=" * 50)

        while True:
            try:
                self.logger.info(f"📄 Scraping de la page {page}...")
                page_start_time = time.time()
                
                projects = self.get_projects(page)
                page_time = time.time() - page_start_time

                if not projects:
                    self.logger.warning(f"❌ Aucun projet trouvé sur la page {page}")
                    self.logger.info("🛑 Arrêt du scraping - Fin des données")
                    break

                all_projects.extend(projects)
                consecutive_errors = 0  # Réinitialiser le compteur d'erreurs
                
                self.logger.info(f"✅ Page {page} terminée en {page_time:.2f}s")
                self.logger.info(f"   - Projets trouvés: {len(projects)}")
                self.logger.info(f"   - Total cumulé: {len(all_projects)}")
                
                page += 1

                # Pause entre les requêtes pour éviter la surcharge
                time.sleep(1)
                self.logger.debug("⏸️ Pause de 1 seconde entre les pages")

                if max_pages and page > max_pages:
                    self.logger.info(f"🏁 Limite de pages atteinte ({max_pages})")
                    break

            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"💥 Erreur sur la page {page}: {str(e)}")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(f"🚨 Trop d'erreurs consécutives ({consecutive_errors})")
                    self.logger.error("🛑 Arrêt forcé du scraping")
                    break
                
                self.logger.warning(f"⏭️ Tentative de continuation (erreur {consecutive_errors}/{max_consecutive_errors})")
                # Pause plus longue en cas d'erreur
                time.sleep(3)
                page += 1

        execution_time = time.time() - start_time
        
        self.logger.info("=" * 50)
        self.logger.info(f"🏆 SCRAPING TERMINÉ")
        self.logger.info(f"   - Projets récupérés: {len(all_projects)}")
        self.logger.info(f"   - Pages traitées: {page - 1}")
        self.logger.info(f"   - Temps total: {execution_time:.2f}s")
        self.logger.info(f"   - Moyenne par page: {execution_time/(page-1):.2f}s")
        self.logger.info("=" * 50)
        
        return [project.to_dict() for project in all_projects]

    def get_projects(self, page):
        """Récupère les projets d'une page donnée avec retry automatique"""
        projects = []
        url = f"{self.base_url}/projets?page={page}"

        for attempt in range(self.max_retry_attempts):
            try:
                self.logger.debug(f"🔄 Tentative {attempt + 1}/{self.max_retry_attempts} - {url}")
                
                response = self.session.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                
                self.logger.debug(f"✅ Réponse HTTP {response.status_code} - Taille: {len(response.content)} bytes")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                project_elements = soup.find_all('div', class_='mission-publish')
                
                self.logger.debug(f"🔍 Trouvé {len(project_elements)} éléments de projet")
                
                success_count = 0
                for i, element in enumerate(project_elements):
                    try:
                        project = self.extract_project_data(element)
                        if project:
                            projects.append(project)
                            success_count += 1
                            self.logger.debug(f"   ✅ Projet {i+1}: {project.title[:30]}...")
                        else:
                            self.logger.debug(f"   ❌ Projet {i+1}: Extraction échouée")
                    except Exception as e:
                        self.logger.warning(f"   ⚠️ Erreur extraction projet {i+1}: {str(e)}")
                        continue

                self.logger.debug(f"📊 Extraction terminée: {success_count}/{len(project_elements)} projets réussis")
                break  # Sortir de la boucle de retry si succès

            except requests.exceptions.Timeout:
                self.logger.warning(f"⏰ Timeout sur {url} (tentative {attempt + 1})")
                if attempt < self.max_retry_attempts - 1:
                    wait_time = 2 ** attempt
                    self.logger.info(f"⏳ Attente de {wait_time}s avant retry...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"🌐 Erreur réseau sur {url}: {str(e)}")
                if attempt < self.max_retry_attempts - 1:
                    wait_time = 2 ** attempt
                    self.logger.info(f"⏳ Attente de {wait_time}s avant retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"💥 Erreur inattendue page {page}: {str(e)}")
                break

        return projects

    def extract_project_data(self, element):
        """Extrait les données d'un projet avec gestion d'erreurs détaillée"""
        try:
            # Titre et URL
            title_tag = element.find('a', class_='text-16 d-block')
            if not title_tag:
                self.logger.debug("❌ Balise titre non trouvée")
                return None
                
            title = title_tag.text.strip()
            url = title_tag.get('href', '')
            
            if not url:
                self.logger.warning(f"❌ URL manquante pour: {title}")
                return None
                
            full_url = url if url.startswith("http") else self.base_url + url

            # Description (depuis page projet)
            description = self.get_project_description(full_url)

            # Budget
            budget_tag = element.find('span', class_='budget')
            budget = budget_tag.text.strip() if budget_tag else "Non spécifié"

            # Date de publication
            date_posted_tag = element.find('span', class_='muted')
            date_posted = date_posted_tag.text.strip() if date_posted_tag else None

            # Deadline
            deadline_tag = element.find('font', class_='ml-1 text-danger')
            deadline = deadline_tag.text.strip() if deadline_tag else None

            project = Project(
                title=title,
                description=description,
                platform="freelancer.ma",
                url=full_url,
                budget=budget,
                date_posted=date_posted,
                deadline=deadline
            )
            
            self.logger.debug(f"✅ Projet extrait: {title[:40]}...")
            return project

        except Exception as e:
            self.logger.error(f"💥 Erreur extraction données: {str(e)}")
            return None

    def get_project_description(self, project_url):
        """Récupère la description d'un projet avec gestion d'erreurs"""
        for attempt in range(2):  # Moins de tentatives pour les descriptions
            try:
                self.logger.debug(f"📄 Récupération description: {project_url[-30:]}")
                
                response = self.session.get(project_url, timeout=self.request_timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                desc_section = soup.find('p', class_='mission-description text-justify text-1')
                
                if desc_section:
                    description = desc_section.get_text(separator=" ").strip()
                    self.logger.debug(f"✅ Description récupérée ({len(description)} chars)")
                    return description
                else:
                    self.logger.debug("❌ Section description non trouvée")
                    
            except requests.exceptions.Timeout:
                self.logger.debug(f"⏰ Timeout description: {project_url[-20:]}")
                if attempt == 0:
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.debug(f"❌ Erreur description: {str(e)}")
                break

        return "Pas de description disponible"