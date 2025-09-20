# Tutoriel : Créer une Skill Alexa "Chat" avec GPT

## 1. Connexion
Connectez-vous à votre compte [Amazon Developer](https://developer.amazon.com/) et ouvrez la **console Alexa Developer**.

---

## 2. Création de la skill
- Cliquez sur **Create Skill**.  
- Donnez-lui le nom **Chat** (ou un autre de votre choix).  
- Sélectionnez la langue principale (**Primary locale**) selon votre préférence.  

---

## 3. Choix du modèle
- Dans **Type of experience**, sélectionnez **Other**.  
- Pour le modèle, choisissez **Custom**.  

---

## 4. Hébergement
Pour les ressources backend, sélectionnez :  
**Alexa-hosted (Python)**.  

---

## 5. Importation de la skill
- Cliquez sur **Import Skill**.  
- Collez le lien suivant :  
  👉 [https://github.com/MiisterNarsikBis/alexa-gpt](https://github.com/MiisterNarsikBis/alexa-gpt)  
- Puis cliquez sur **Import**.  

---

## 6. Éditeur JSON
Dans la section **Build**, ouvrez l’onglet **JSON Editor**.  

---

## 7. Configuration de l’invocation
- Si vous avez importé la skill depuis le dépôt GitHub :  
  👉 Changez simplement `"invocationName"` par **chat** (ou un mot de votre choix).  
  Passez ensuite directement à l’étape 12.  

- Si vous avez choisi de **créer la skill manuellement** :  
  Remplacez le contenu JSON par celui-ci :  

```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "chat",
      "intents": [
        {
          "name": "GptQueryIntent",
          "slots": [
            {
              "name": "query",
              "type": "AMAZON.Person"
            }
          ],
          "samples": [
            "{query}"
          ]
        },
        {
          "name": "AMAZON.CancelIntent",
          "samples": []
        },
        {
          "name": "AMAZON.HelpIntent",
          "samples": []
        },
        {
          "name": "AMAZON.StopIntent",
          "samples": []
        },
        {
          "name": "AMAZON.NavigateHomeIntent",
          "samples": []
        }
      ],
      "types": []
    }
  }
}

## 8. Sauvegarde et construction
Cliquez sur **Save Model**, puis sur **Build Model** pour générer le modèle.  

---

## 9. Création d’une clé OpenAI
- Rendez-vous dans votre compte OpenAI, section **API keys**.  
- Cliquez sur **+ Create new secret key** pour générer une clé.  

---

## 12. Ajout de la clé API
Ajoutez la clé OpenAI obtenue dans la variable :  
**openai_api_key**.  

---

## 13. Activation en mode développement
- Sauvegardez et déployez.  
- Allez dans la section **Test**.  
- Activez **Skill testing in Development**.  

---

## 14. Utilisation
Votre Alexa est maintenant prête à fonctionner en **mode ChatGPT** 🎉  
Vous devriez voir apparaître des réponses similaires à celles du modèle ChatGPT.  