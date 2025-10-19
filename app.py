import streamlit as st
import tempfile
from utils import extract_text_from_pdf
from analyze import analyze_candidate
import json
import time

# ------------------------------------------------------
# 🧠 CONFIGURATION DE BASE
# ------------------------------------------------------
st.set_page_config(page_title="IA Recruiter Assistant", page_icon="🤖", layout="wide")

st.title("Assistant de recrutement")
st.caption("Analyse par inteligence artificielle")

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

        st.success("✅ Analyse terminée avec succès !")

        # ------------------------------------------------------
        # 🔍 AFFICHAGE VISUEL UNIQUEMENT (plus de texte brut)
        # ------------------------------------------------------
        try:
            result = json.loads(result_text)

            st.header("📊 Tableau de bord du candidat")

            # === Résumé global ===
            st.subheader("Résumé global")
            st.write(result.get("resume", "—"))

            # === Points forts / faibles ===
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ Points forts")
                for pf in result.get("points_forts", []):
                    st.markdown(f"- {pf}")
            with col2:
                st.markdown("### ⚠️ Points faibles")
                for pf in result.get("points_faibles", []):
                    st.markdown(f"- {pf}")

            # === Évaluation par axe (barres modernes animées) ===
            st.markdown("###  Résumé des évaluations")

            notes = result.get("notes", {})
            if notes:
                # --- Style CSS moderne ---
                st.markdown("""
                    <style>
                    .progress-container {
                        width: 100%;
                        background-color: #1E1E1E;
                        border-radius: 10px;
                        margin-bottom: 12px;
                        padding: 6px 10px;
                    }
                    .progress-label {
                        display: flex;
                        justify-content: space-between;
                        font-size: 0.9rem;
                        color: #D0D0D0;
                        margin-bottom: 4px;
                    }
                    .progress-bar {
                        height: 10px;
                        border-radius: 10px;
                        transition: width 1s ease-out;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # --- Affichage animé ---
                for skill, value in notes.items():
                    color = "#2E8BFF" if value >= 7 else "#F1C40F" if value >= 5 else "#E74C3C"
                    width = int((value / 10) * 100)

                    progress_html = f"""
                    <div class="progress-container">
                        <div class="progress-label">
                            <span>{skill}</span>
                            <span>{value:.1f}/10</span>
                        </div>
                        <div class="progress-bar" style="width:0%; background-color:{color};"></div>
                    </div>
                    """

                    placeholder = st.empty()
                    placeholder.markdown(progress_html, unsafe_allow_html=True)
                    time.sleep(0.05)
                    placeholder.markdown(
                        progress_html.replace('width:0%', f'width:{width}%'),
                        unsafe_allow_html=True
                    )

           # === 🏁 SECTION : Synthèse finale ===
            st.markdown("### Verdict de l’analyse IA")

            st.markdown("""
                <style>
                .summary-card {
                    border-radius: 12px;
                    padding: 25px 30px;
                    margin-top: 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .summary-item {
                    text-align: center;
                    flex: 1;
                }
                .summary-score {
                    font-size: 2.8rem;
                    font-weight: 700;
                    color: #2E8BFF;
                    margin: 0;
                    line-height: 1;
                }
                .summary-label {
                    font-size: 0.95rem;
                    color: #BBBBBB;
                    margin-top: 6px;
                }
                .verdict-icon {
                    font-size: 2rem;
                    display: block;
                    margin-bottom: 4px;
                }
                .verdict-text {
                    font-size: 1.3rem;
                    font-weight: 600;
                    color: #FFD700;
                    margin: 0;
                }
                </style>
            """, unsafe_allow_html=True)

            # Données
            note_globale = result.get("global", "—")
            verdict = result.get("verdict", "—")

            # Couleur selon verdict
            verdict_color = (
                "#2ECC71" if "🟢" in verdict else
                "#F1C40F" if "🟡" in verdict else
                "#E74C3C"
            )

            verdict_icon = (
                "🟢" if "🟢" in verdict else
                "🟡" if "🟡" in verdict else
                "🔴"
            )

            verdict_text = verdict.replace(verdict_icon, "").strip()

            # Affichage harmonieux
            summary_html = f"""
            <div class="summary-card">
                <div class="summary-item">
                    <p class="summary-score">{note_globale}/10</p>
                    <p class="summary-label">Note globale</p>
                </div>
                <div class="summary-item">
                    <span class="verdict-icon">{verdict_icon}</span>
                    <p class="verdict-text" style="color:{verdict_color};">{verdict_text}</p>
                    <p class="summary-label">Recommandation</p>
                </div>
            </div>
            """
            st.markdown(summary_html, unsafe_allow_html=True)


        except Exception as e:
            st.error("❌ Erreur lors de la lecture du résultat IA.")
            st.caption(str(e))
