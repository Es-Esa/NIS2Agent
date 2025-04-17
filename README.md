# 🛡️ NIS2Agent – Tietoturva-automaatiobotti NIS2-direktiivin mukaisiin tarkastuksiin (Proof of concept)          

**NIS2Agent** on kevyt, täysin laajennettavissa, automatisoitu tietoturva-analyysityökalu, joka auttaa organisaatioita tunnistamaan ja analysoimaan järjestelmäraportteja tekoälyn avulla. Se on suunniteltu vastaamaan Suomen uuden tietoturvalain ja EU:n NIS2-direktiivin vaatimuksia.
---

## 🔍 Projektin tarkoitus

NIS2Agent koostuu kahdesta pääosasta:

- **Agentti** (asennetaan tarkastettavaan koneeseen): lukee tietoturvaraportit, suorittaa esianalyysin ja lähettää tiivistetyn datan tekoälymallille analysoitavaksi.
- **Palvelin (LLM)**: suorittaa luonnollisen kielen analyysin ja ehdottaa parannuksia, havaitsee tietoturvapuutteita ja raportoi tulokset takaisin.

---

## 🧰 Teknologiat ja kirjastot

| Komponentti       | Kuvaus                                 |
|-------------------|------------------------------------------|
| Python            | Agentin pääohjelmointikieli              |
| Open Source LLM   | Paikallinen LLM-palvelin (esim. LM Studio, Mistral, Ollama) |
| JSON              | Raporttien tiedostomuoto                 |
| REST API          | Kommunikaatio agentin ja LLM:n välillä   |

---

## 🧪 Esivaatimukset

- **Python 3.8+**
- **LM Studio** tai muu yhteensopiva LLM, esim. `lily-cybersecurity-7b-v0.2`
- Tietoturvaraportteja JSON-muodossa

---

## 📦 Asennus

1. **Kloonaa projekti**
```bash
git clone https://github.com/Es-Esa/NIS2Agent.git
cd nis2bot

    Asenna riippuvuudet (valinnainen, jos käytetään ulkopuolisia kirjastoja myöhemmin)

pip install -r requirements.txt

    Käynnistä LLM-palvelin (esim. LM Studio)

        Aseta malli käyttöön (lily-cybersecurity-7b-v0.2)

        Varmista että LLM toimii osoitteessa http://localhost:1234/v1/chat/completions

    Aseta raportit kansioon

backend/reports/

    Suorita agentti

cd agent
python NIS2Bot.py

📁 Projektin rakenne

nis2bot/
│
├── agent/                     # Agentti, joka analysoi raportit
│   └── NIS2Bot.py             # Päälogiikka
│
├── backend/
│   └── reports/               # JSON-raportit tänne
│       └── AICHECK/           # AI-analyysin tulokset tallennetaan tänne
│
└── README.md  
