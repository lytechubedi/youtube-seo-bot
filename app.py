import os
import re
import json
import requests
import google.generativeai as genai

# 1. Configuration de l'IA Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Erreur : La clé GEMINI_API_KEY est manquante.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

def fetch_youtube_trends(search_query):
    print(f"🔍 Recherche des tendances YouTube pour : '{search_query}'...")
    url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Impossible d'accéder à YouTube (Code: {response.status_code})")
            return []
        
        # Extraction des données JSON cachées dans la page YouTube
        json_data = re.search(r"ytInitialData\s*=\s*({.+?});", response.text)
        if not json_data:
            print("❌ Impossible de parser les données initiales de YouTube.")
            return []
            
        data = json.loads(json_data.group(1))
        videos = []
        
        # Parcours de la structure de l'arbre JSON de YouTube pour extraire titres et descriptions
        contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        
        for item in contents:
            if "videoRenderer" in item:
                video_renderer = item["videoRenderer"]
                title = video_renderer["title"]["runs"][0]["text"]
                
                # Récupération de la description si elle existe
                description = ""
                if "detailedMetadataSnippets" in video_renderer:
                    snippets = video_renderer["detailedMetadataSnippets"]
                    if snippets and "snippetText" in snippets[0]:
                        description = snippets[0]["snippetText"]["runs"][0]["text"]
                
                videos.append({"title": title, "description": description})
                if len(videos) >= 5: # On s'arrête aux 5 vidéos les plus pertinentes
                    break
                    
        return videos
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping : {str(e)}")
        return []

def main():
    # Les deux niches combinées : Finance/IA + Business/Motivation
    query = "intelligence artificielle business automatisation motivation"
    trending_videos = fetch_youtube_trends(query)
    
    if not trending_videos:
        print("❌ Aucune donnée récoltée. Arrêt du script.")
        return

    # Construction du bloc de texte pour le prompt
    context_data = ""
    for idx, vid in enumerate(trending_videos, 1):
        context_data += f"Vidéo {idx} -\nTitre: {vid['title']}\nDescription: {vid['description']}\n\n"

    # 2. Rédaction du prompt pour Gemini
    prompt = f"""
    Tu es le meilleur expert mondial en SEO YouTube et en ingénierie algorithmique.
    Voici les titres et descriptions des vidéos qui font le plus de vues actuellement sur la thématique combinée (IA/Business/Automatisation) :
    
    {context_data}
    
    En te basant rigoureusement sur ces données à succès, génère un rapport stratégique en français contenant :
    
    1. **ANALYSE DES MOTS-CLÉS :** Liste les mots-clés exacts qui déclenchent l'algorithme en ce moment.
    2. **3 PROPOSITIONS DE TITRES ULTRA-VRAUX :** Des titres percutants, mystérieux ou axés sur le gain, parfaits pour une vidéo face caméra.
    3. **DESCRIPTION OPTIMISÉE (PRÊTE À COPIER-COLLER) :** Rédige une description complète (environ 200-300 mots) optimisée pour le SEO. Elle doit inclure naturellement les mots-clés, un sommaire fictif, et des appels à l'action clairs.
    4. **TAGS (SÉPARÉS PAR DES VIRGULES) :** Une liste de 20 tags pertinents prêts pour la case tags de YouTube.
    
    Fournis une réponse propre, bien formatée en Markdown.
    """

    print("🤖 Envoi des données à l'IA Gemini pour optimisation...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    # 3. Écriture du fichier final de sortie
    output_file = "briefing_seo.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print(f"💾 Succès total ! Le fichier '{output_file}' a été mis à jour.")

if __name__ == "__main__":
    main()

