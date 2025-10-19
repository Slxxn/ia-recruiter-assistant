import streamlit as st
import tempfile
import matplotlib.pyplot as plt
from utils import extract_text_from_pdf
from analyze import analyze_candidate
import re
import json

# ------------------------------------------------------
# 🧠 CONFIGURATION DE BASE
# ------------------------------------------------------
st.set_page_config(page_title="IA Recruiter Assistant", page_icon="🤖", layout="wide")

st.title("🤖 IA Recruiter Assistant")
st.caption("Analyse intelligente de candidatures — IA RH (CV, fiche de poste, lettre de motivation)")

# ------------------------------------------------------
# 📄 SECTION 1 : Fiche de poste
# ------------------------------------------------------
st.subheader("📋 Fiche de poste (facultative)")
job_description = st.text_area("Colle ici la description du poste :", height=150)

# ------------------------------------------------------
# 📂 SECTION 2 : Fichiers du candidat
# ------------------------------------------------------
st.subheader("📂 Candidature du candidat")

cv_file = st.file_uploader("Importe le CV (PDF)", type=["pdf"])
letter_file = st.file_uploader("Importe la lettre de motivation (PDF ou TXT)", type=["pdf", "txt"])

# ------------------------------------------------------
# 🚀 SECTION 3 : Lancement de l’analyse
# ------------------------------------------------------
if st.button("Analyser la candidature", use_container_width=True):
    if not cv_file and not job_description:
        st.warning("⚠️ Merci d’ajouter au moins le CV ou la fiche de poste avant de lancer l’analyse.")
    else:
        with st.spinner("Analyse en cours... ⏳"):
            cv_text, letter_text = "", ""

            # Lecture du CV
            if cv_file:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_cv:
                    tmp_cv.write(cv_file.read())
                    cv_text = extract_text_from_pdf(tmp_cv.name)

            # Lecture de la lettre
            if letter_file:
                if letter_file.name.endswith(".pdf"):
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_letter:
                        tmp_letter.write(letter_file.read())
                        letter_text = extract_text_from_pdf(tmp_letter.name)
                else:
                    letter_text = letter_file.read().decode("utf-8")

            # Analyse IA
            result_text = analyze_candidate(
                cv_text=cv_text or None,
                job_title=job_description or None,
                letter_text=letter_text or None
            )

        # ------------------------------------------------------
        # 🔍 Affichage clair du résultat
        # ------------------------------------------------------
        st.success("✅ Analyse terminée avec succès !")

        # Tentative de formatage automatique (si JSON détecté)
        try:
            result = json.loads(result_text)
            # Si l’IA renvoie un JSON propre
            st.header("📊 Tableau de bord du candidat")

            # --- Résumé global ---
            st.subheader("🧾 Résumé global")
            st.write(result.get("resume", "—"))

            # --- Points forts / faibles ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ Points forts")
                for pf in result.get("points_forts", []):
                    st.markdown(f"- {pf}")
            with col2:
                st.markdown("### ⚠️ Points faibles")
                for pf in result.get("points_faibles", []):
                    st.markdown(f"- {pf}")

            # --- Graphique des notes ---
            st.markdown("### 📈 Évaluation par axe")
            notes = result.get("notes", {})
            if notes:
                labels = list(notes.keys())
                values = list(notes.values())

                fig, ax = plt.subplots(figsize=(6, 3))
                ax.barh(labels, values, color="#4a90e2")
                ax.set_xlim(0, 10)
                ax.set_xlabel("Note /10")
                ax.set_title("Évaluation des compétences")
                st.pyplot(fig)

            # --- Note globale et verdict ---
            colA, colB = st.columns(2)
            with colA:
                st.metric("⭐ Note globale", f"{result.get('global', '—')}/10")
            with colB:
                st.metric("🏁 Recommandation", result.get("verdict", "—"))

        except Exception:
            # Si le retour n’est pas structuré (texte brut)
            st.markdown("### 🧠 Résultat de l'analyse (texte brut)")
            st.markdown(result_text)
