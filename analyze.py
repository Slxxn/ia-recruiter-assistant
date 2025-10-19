import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_candidate(cv_text=None, job_title=None, letter_text=None):
    """
    Analyse une candidature de manière contextuelle, cohérente et robuste.
    - Corrige automatiquement les erreurs JSON de sortie.
    - Pondère les notes selon le type de poste.
    - Génère un verdict cohérent avec les scores.
    """

    # Vérification minimale
    if not cv_text and not job_title:
        return json.dumps({
            "resume": "Aucune donnée fournie.",
            "points_forts": [],
            "points_faibles": ["Il faut au moins un CV ou un intitulé de poste."],
            "notes": {
                "Compétences techniques": 0,
                "Expérience et réalisations": 0,
                "Qualités humaines / Soft skills": 0,
                "Motivation et adéquation au poste": 0,
                "Potentiel d’évolution": 0
            },
            "global": 0,
            "verdict": "🟡 À approfondir"
        }, ensure_ascii=False)

    # --- Contexte dynamique ---
    context = ""
    if job_title:
        context += f"POSTE CIBLE : {job_title}\n---\n"
    if cv_text:
        context += f"CV DU CANDIDAT :\n{cv_text}\n---\n"
    if letter_text:
        context += f"LETTRE DE MOTIVATION :\n{letter_text}\n---\n"
    else:
        context += "Aucune lettre de motivation fournie.\n---\n"

    # --- Détection du type de poste (pour pondération) ---
    job_title_lower = job_title.lower() if job_title else ""
    if any(word in job_title_lower for word in ["vendeur", "commercial", "accueil", "client", "communication", "service"]):
        job_type = "commercial"
    elif any(word in job_title_lower for word in ["développeur", "technicien", "ingénieur", "data", "maintenance", "informatique"]):
        job_type = "technique"
    else:
        job_type = "mixte"

    # --- Prompt IA ---
    prompt = f"""
Tu es un recruteur IA professionnel. Analyse le profil ci-dessous en lien avec le poste ciblé.

Données :
{context}

🎯 Objectif :
- Les points forts doivent expliquer pourquoi certaines compétences ou expériences sont pertinentes pour le poste.
- Les points faibles doivent pointer uniquement les manques réels ou axes d'amélioration.
- Ne te contredis jamais : si le CV prouve une compétence, ne la considère pas comme un manque.
- Si le candidat a déjà travaillé dans le même poste ou la même entreprise, considère cela comme un atout majeur.
- Les notes doivent refléter l’adéquation réelle au poste.
- Pondération implicite selon le type de poste :
  • Poste commercial → plus de poids sur Soft Skills & Motivation
  • Poste technique → plus de poids sur Compétences & Expérience
  • Poste mixte → équilibre les critères

📋 FORMAT DE SORTIE (JSON STRICT UNIQUEMENT) :
{{
  "resume": "Résumé global du candidat (3–5 lignes).",
  "points_forts": [
    "Compétence ou expérience — explication de sa pertinence pour le poste."
  ],
  "points_faibles": [
    "Manque ou faiblesse — pourquoi c’est un frein pour ce poste."
  ],
  "notes": {{
    "Compétences techniques": nombre,
    "Expérience et réalisations": nombre,
    "Qualités humaines / Soft skills": nombre,
    "Motivation et adéquation au poste": nombre,
    "Potentiel d’évolution": nombre
  }}
}}

Réponds uniquement avec le JSON.
"""

    try:
        # --- Appel au modèle ---
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw_output = completion.choices[0].message.content.strip()
        json_part = raw_output[raw_output.find("{"): raw_output.rfind("}") + 1]

        # --- Nettoyage automatique du JSON ---
        json_part = json_part.replace("\n", " ")
        json_part = re.sub(r"\s+", " ", json_part)
        json_part = json_part.replace("’", "'")
        json_part = json_part.replace("«", '"').replace("»", '"')

        # --- Parsing tolérant ---
        try:
            data = json.loads(json_part)
        except json.JSONDecodeError:
            try:
                import simplejson as sjson
                data = sjson.loads(json_part, strict=False)
            except Exception:
                return json.dumps({
                    "resume": "Erreur lors de l'analyse (format JSON illisible).",
                    "points_forts": [],
                    "points_faibles": [],
                    "notes": {},
                    "global": 0,
                    "verdict": "🟡 À approfondir"
                }, ensure_ascii=False)

        # --- Normalisation des notes ---
        data.setdefault("notes", {})
        for k in [
            "Compétences techniques",
            "Expérience et réalisations",
            "Qualités humaines / Soft skills",
            "Motivation et adéquation au poste",
            "Potentiel d’évolution"
        ]:
            data["notes"].setdefault(k, 0)

        # --- Pondération par type de poste ---
        weights = {
            "commercial": {
                "Compétences techniques": 0.8,
                "Expérience et réalisations": 1.0,
                "Qualités humaines / Soft skills": 1.2,
                "Motivation et adéquation au poste": 1.3,
                "Potentiel d’évolution": 1.0
            },
            "technique": {
                "Compétences techniques": 1.3,
                "Expérience et réalisations": 1.2,
                "Qualités humaines / Soft skills": 0.8,
                "Motivation et adéquation au poste": 0.9,
                "Potentiel d’évolution": 1.0
            },
            "mixte": {
                "Compétences techniques": 1.0,
                "Expérience et réalisations": 1.0,
                "Qualités humaines / Soft skills": 1.0,
                "Motivation et adéquation au poste": 1.0,
                "Potentiel d’évolution": 1.0
            }
        }

        w = weights.get(job_type, weights["mixte"])
        total_score, total_weight = 0, 0
        for key, score in data["notes"].items():
            total_score += score * w.get(key, 1)
            total_weight += w.get(key, 1)
        data["global"] = round(total_score / total_weight, 1) if total_weight > 0 else 0

        # --- Verdict automatique ---
        if data["global"] >= 7:
            data["verdict"] = "🟢 À retenir"
        elif data["global"] >= 4:
            data["verdict"] = "🟡 À approfondir"
        else:
            data["verdict"] = "🔴 Non pertinent"

        return json.dumps(data, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "resume": "Erreur lors de l'analyse.",
            "points_forts": [],
            "points_faibles": [str(e)],
            "notes": {},
            "global": 0,
            "verdict": "🟡 À approfondir"
        }, ensure_ascii=False)
