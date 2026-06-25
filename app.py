import streamlit as st
from datetime import datetime
import json
import os

# Nom du fichier de sauvegarde sur le Bureau
DB_FILE = "hansave_db.json"

# --- 1. FONCTIONS DE SAUVEGARDE ET CHARGEMENT (PERMANENCE) ---
def charger_donnees():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Base de données initiale par défaut si le fichier n'existe pas encore
        return {
            "HS-101": {
                "nom": "Woodso", 
                "solde": 1500.0, 
                "code": "1234",
                "transactions": [{"date": "2026-06-25 10:30", "type": "Dépôt Initial", "montant": 1500.0}]
            },
            "HS-102": {
                "nom": "Marie", 
                "solde": 2750.0, 
                "code": "5678",
                "transactions": [{"date": "2026-06-25 11:15", "type": "Dépôt Initial", "montant": 2750.0}]
            }
        }

def sauvegarder_donnees(donnees):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

# Chargement initial des données dans la session Streamlit
if "comptes" not in st.session_state:
    st.session_state.comptes = charger_donnees()

# --- 2. BARRE LATÉRALE & SÉCURITÉ ADMIN ---
st.sidebar.title("💳 Menu Hansave")
page = st.sidebar.radio("Navigation :", ["Espace Client", "Espace Admin (Toi)"])

# --- 3. PAGE : ESPACE CLIENT ---
if page == "Espace Client":
    st.title("🏦 Plateforme Hansave")
    st.subheader("Gérez votre argent en toute liberté")
    st.write("---")

    with st.form("form_verification"):
        st.write("### 🔑 Connexion Client")
        numero_compte = st.text_input("Numéro de compte (ex: HS-101)").strip()
        code_secret = st.text_input("Code secret", type="password").strip()
        bouton_valider = st.form_submit_button("Accéder à mon espace")

    if bouton_valider:
        if numero_compte in st.session_state.comptes:
            client = st.session_state.comptes[numero_compte]
            if client["code"] == code_secret:
                st.session_state["client_connecte"] = numero_compte
                st.success(f"Bienvenue, {client['nom']} !")
            else:
                st.error("Code secret incorrect.")
        else:
            st.error("Ce numéro de compte n'existe pas.")

    # Si le client est connecté avec succès
    if "client_connecte" in st.session_state:
        compte_actuel = st.session_state["client_connecte"]
        client = st.session_state.comptes[compte_actuel]
        
        st.write("---")
        st.metric(label="Votre solde actuel", value=f"{client['solde']:,} HTG".replace(",", " "))
        
        # ZONE : TRANSFERT D'ARGENT
        with st.expander("💸 Faire un transfert d'argent"):
            compte_destinataire = st.text_input("Numéro de compte du bénéficiaire").strip()
            montant_transfert = st.number_input("Montant à transférer (HTG)", min_value=1.0, step=50.0)
            
            if st.button("Confirmer le transfert"):
                if compte_destinataire in st.session_state.comptes:
                    if compte_destinataire != compte_actuel:
                        if client["solde"] >= montant_transfert:
                            date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            # Débit du client actuel
                            client["solde"] -= montant_transfert
                            client["transactions"].append({"date": date_actuelle, "type": f"Transfert vers {compte_destinataire}", "montant": montant_transfert})
                            
                            # Crédit du destinataire
                            st.session_state.comptes[compte_destinataire]["solde"] += montant_transfert
                            st.session_state.comptes[compte_destinataire]["transactions"].append({"date": date_actuelle, "type": f"Transfert reçu de {client['nom']}", "montant": montant_transfert})
                            
                            # Sauvegarde
                            sauvegarder_donnees(st.session_state.comptes)
                            st.success(f"Transfert de {montant_transfert} HTG envoyé avec succès à {st.session_state.comptes[compte_destinataire]['nom']} !")
                            st.rerun()
                        else:
                            st.error("Solde insuffisant pour ce transfert.")
                    else:
                        st.warning("Vous ne pouvez pas vous envoyer de l'argent à vous-même.")
                else:
                    st.error("Le compte destinataire n'existe pas.")

        # ZONE : HISTORIQUE DES TRANSACTIONS
        st.write("### 📜 Vos dernières opérations")
        for t in reversed(client["transactions"]):
            if "Dépôt" in t["type"] or "reçu" in t["type"]:
                couleur = "🟢"
            else:
                couleur = "🔴"
            st.write(f"{couleur} **{t['date']}** | {t['type']} : **{t['montant']:,} HTG**".replace(",", " "))

# --- 4. PAGE : ESPACE ADMIN (TOI) ---
elif page == "Espace Admin (Toi)":
    st.title("🛠️ Panneau de Contrôle Hansave")
    st.write("---")

    # Protection par mot de passe Admin
    mot_de_passe_admin = st.text_input("Entrez le code secret Administrateur pour déverrouiller :", type="password")
    
    # Remplacer 'admin2026' par le mot de passe de ton choix
    if mot_de_passe_admin == "admin2026":
        st.success("Accès autorisé, Bonjour Patron !")
        
        # STATISTIQUES EN HAUT
        total_comptes = len(st.session_state.comptes)
        liquidite_totale = sum(c["solde"] for c in st.session_state.comptes.values())
        
        col1, col2 = st.columns(2)
        col1.metric("Clients Inscrits", f"{total_comptes}")
        col2.metric("Liquidités Totales (Fonds)", f"{liquidite_totale:,} HTG".replace(",", " "))
        
        st.write("---")
        onglet_operation, onglet_nouveau = st.tabs(["💰 Dépôts / Retraits", "👤 Créer un Nouveau Client"])

        # Admin Action 1 : Enregistrer un Dépôt ou Retrait
        with onglet_operation:
            compte_cible = st.selectbox("Sélectionner le client", list(st.session_state.comptes.keys()))
            type_op = st.selectbox("Opération", ["Dépôt", "Retrait"])
            montant = st.number_input("Montant (HTG)", min_value=1.0, step=100.0)
            
            if st.button("Valider l'opération"):
                client = st.session_state.comptes[compte_cible]
                date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                if type_op == "Dépôt":
                    client["solde"] += montant
                    client["transactions"].append({"date": date_actuelle, "type": "Dépôt (Banque)", "montant": montant})
                    sauvegarder_donnees(st.session_state.comptes)
                    st.success(f"Dépôt de {montant} HTG effectué.")
                    st.rerun()
                elif type_op == "Retrait":
                    if client["solde"] >= montant:
                        client["solde"] -= montant
                        client["transactions"].append({"date": date_actuelle, "type": "Retrait (Banque)", "montant": montant})
                        sauvegarder_donnees(st.session_state.comptes)
                        st.success(f"Retrait de {montant} HTG effectué.")
                        st.rerun()
                    else:
                        st.error("Fonds insuffisants sur le compte du client.")

        # Admin Action 2 : Créer un client
        with onglet_nouveau:
            nouveau_id = st.text_input("Numéro de compte unique (ex: HS-103)").strip()
            nouveau_nom = st.text_input("Nom Complet").strip()
            nouveau_code = st.text_input("Code secret du client (4 chiffres)", max_chars=4).strip()
            solde_initial = st.number_input("Dépôt initial (HTG)", min_value=0.0, step=500.0)

            if st.button("Enregistrer le client"):
                if nouveau_id and nouveau_nom and nouveau_code:
                    if nouveau_id not in st.session_state.comptes:
                        date_c = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state.comptes[nouveau_id] = {
                            "nom": nouveau_nom,
                            "solde": solde_initial,
                            "code": nouveau_code,
                            "transactions": [{"date": date_c, "type": "Ouverture de compte", "montant": solde_initial}] if solde_initial > 0 else []
                        }
                        sauvegarder_donnees(st.session_state.comptes)
                        st.success(f"Le compte {nouveau_id} a été sauvegardé avec succès !")
                        st.rerun()
                    else:
                        st.error("Cet identifiant de compte existe déjà.")
                else:
                    st.warning("Veuillez remplir toutes les informations.")
    else:
        if mot_de_passe_admin != "":
            st.error("Mot de passe Administrateur incorrect.")