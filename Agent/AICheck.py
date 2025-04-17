import os
import json
import requests

# Määritellään hakemistopolut Agent-kansiossa
agent_folder = os.path.dirname(os.path.abspath(__file__))  # Agent-kansion polku
backend_folder = os.path.abspath(os.path.join(agent_folder, '..', 'backend'))  # Backend-kansion polku

# Input ja output polut backendin kautta
input_folder = os.path.join(backend_folder, 'reports')  # Raportit ovat tässä hakemistossa
output_folder = os.path.join(backend_folder, 'reports', 'AICHECK')  # AICHECK-kansio tuloksille

# Luo AICHECK-kansio, jos sitä ei ole olemassa
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Funktio, joka suorittaa tekoälyn tarkistuksen ja tallentaa tuloksen tiedostoon
def run_ai_check(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        report_content = file.read()  # Luetaan sisältö merkkijonona

    try:
        report_data = json.loads(report_content)  # Jäsennetään JSON merkkijonosta
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {os.path.basename(file_path)}: {e}")
        return  # Poistutaan, jos JSON on virheellinen

    # Valitaan vain olennaiset kentät analyysiä varten
    essential_data = {
        "login": report_data.get("login"),
        "users": report_data.get("users"),
        "security_flaws": report_data.get("security_flaws"),
        "warnings": report_data.get("warnings"),
        "errors": report_data.get("errors"),
        "network": report_data.get("network"),
    }

    # Poistetaan tyhjät kentät
    essential_data = {k: v for k, v in essential_data.items() if v}

    # Sarjoitetaan tiivistetty JSON analyysiä varten
    serialized = json.dumps(essential_data, indent=2)

    # Tarkistetaan, ettei sisältö ole liian pitkä
    MAX_LENGTH = 5000
    if len(serialized) > MAX_LENGTH:
        print(f"Skipping {os.path.basename(file_path)}: trimmed content still too long ({len(serialized)} chars).")
        return

    # Promptin rakennus tekoälylle
    payload = {
        "model": "lily-cybersecurity-7b-v0.2",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Analyze the following trimmed security report for critical issues, vulnerabilities, "
                    "and flaws. Focus on login mechanisms, user accounts, network risks, and give suggestions "
                    "to improve the system's security posture.\n\n"
                    f"{serialized}"
                )
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

    # Lähetetään pyyntö tekoälylle
    response = requests.post("http://localhost:1234/v1/chat/completions", json=payload)

    if response.status_code == 200:
        ai_response = response.json()
        ai_suggestions = ai_response.get('choices', [{}])[0].get('message', {}).get('content', 'No response')

        # Tallenna tekoälyn ehdotukset tiedostoon
        output_file_path = os.path.join(output_folder, os.path.basename(file_path) + '_AI_CHECK.txt')
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(ai_suggestions)

        print(f"Tulokset tallennettu tiedostoon: {output_file_path}")
    else:
        print(f"Virhe tekoälyn vastauksessa: {response.status_code} - {response.text}")

# Haetaan kaikki JSON-raportit reports-hakemistosta
for filename in os.listdir(input_folder):
    file_path = os.path.join(input_folder, filename)

    # Suoritetaan tarkistus vain jos tiedosto on .json -tiedosto
    if os.path.isfile(file_path) and filename.endswith('.json'):
        print(f"Suoritetaan tarkistus tiedostolle: {filename}")
        run_ai_check(file_path)
