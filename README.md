# Fredagsbar-event-system

Et system til at holde styr på fredagsbarens events og tilmeldinger. Et event
har et begrænset antal pladser, og API'en afviser tilmeldinger, når det er fuldt.

- **API**: Flask, data i hukommelsen
- **Frontend**: Streamlit, taler med API'en via httpx
- **Kørsel**: lokalt i to terminaler, eller samlet med `docker compose up`

## Filer

| Fil | Indhold |
| --- | --- |
| `api.py` | Flask-API'en med de seks endpoints |
| `swagger.json` | OpenAPI 3.0-dokumentation af alle endpoints og fejlkoder |
| `app.py` | Streamlit-frontenden |
| `Dockerfile` | Bruges af begge services |
| `docker-compose.yml` | Starter API og frontend sammen |
| `.dockerignore` | Holder `.venv` og `.git` ude af image'et |

## Kør lokalt

```bash
uv sync
```

Terminal 1 — API'en:

```bash
uv run api.py
```

Terminal 2 — frontenden:

```bash
uv run streamlit run app.py
```

Frontenden åbner på <http://localhost:8501>, API'en svarer på
<http://localhost:5000>.

## Kør med Docker

```bash
docker compose up --build
```

| Service | Port | Adresse |
| --- | --- | --- |
| Frontend | 8501 | <http://localhost:8501> |
| API | **5000** | <http://localhost:5000> — brug denne i Postman |

Begge porte er publiceret til værtsmaskinen, så API'en kan testes i Postman,
mens den kører i Docker.

## Endpoints

| Metode | URL | Body | Succes |
| --- | --- | --- | --- |
| GET | `/events` | – | 200 + liste |
| GET | `/events/<id>` | – | 200 + ét event |
| POST | `/events` | `{"title", "date", "capacity"}` | 201 + det nye event |
| POST | `/events/<id>/signups` | `{"name"}` | 201 + det opdaterede event |
| DELETE | `/events/<id>/signups/<name>` | – | 204 |
| DELETE | `/events/<id>` | – | 204 |

Derudover findes `GET /debug/slow`, som med vilje svarer efter fem sekunder.
Den bruges til at afprøve frontendens timeout og hører ikke til selve systemet.

### Fejlkoder

| Situation | Kode |
| --- | --- |
| Eventet findes ikke | 404 |
| Tilmeldingen findes ikke ved afmelding | 404 |
| `title` eller `date` mangler, eller `capacity` er ikke et positivt heltal | 400 |
| Tilmelding uden `name` | 400 |
| Eventet er fuldt | 409 |
| Personen er allerede tilmeldt | 409 |

Alle fejl svarer med en JSON-body på formen `{"error": "..."}`.

## Valg undervejs

**API'ens adresse kommer fra miljøvariablen `API_URL`.** Lokalt rammer
frontenden `http://127.0.0.1:5000`, som er standardværdien. I Docker sætter
`docker-compose.yml` den til `http://api:5000`, hvor `api` er navnet på den
anden service. Inde i en container er `127.0.0.1` containeren selv, så
adressen *skal* være forskellig de to steder — og derfor må den ikke stå fast
i koden.

**Begge servere lytter på `0.0.0.0`.** Standarden er `127.0.0.1`, og en
container, der kun lytter der, kan ikke nås udefra, uanset hvilke porte der
publiceres.

**Selectboxen vælger på `id`, ikke på hele eventet.** Streamlit gemmer det
valgte element mellem kørsler. Gav man den hele dictionaries, ville widget'en
holde fast i den gamle udgave hen over `st.rerun()`, og deltagerlisten ville
vise forældede tal, indtil siden blev genindlæst. Et `id` er et tal, der ikke
ændrer sig, når eventet får en ny deltager.

**Data hentes ved hver kørsel af scriptet.** Streamlit kører hele filen forfra
ved hvert klik, så `GET /events` sker hver gang. Det er grunden til, at
oversigten altid viser det rigtige antal lige efter en tilmelding.

**Kun et fuldt event slår tilmeldingsknappen fra.** Tomt navn og
dobbelttilmelding sendes med vilje videre til API'en, så dens 400 og 409 kan
ses i brugerfladen. Ellers ville fejlhåndteringen kun kunne afprøves i Postman.

**`ConnectTimeout` håndteres sammen med `ConnectError`.** Linux afviser en
forbindelse til en død port med det samme, mens Windows lader den løbe ud.
De to styresystemer kaster hver sin undtagelse for samme situation, så begge
skal give beskeden om, at serveren ikke kører. `ConnectTimeout` står først i
`except`, fordi den også er en `TimeoutException` og ellers ville blive fanget
af den bredere linje nedenunder.

**Data ligger i hukommelsen.** Alt nulstilles, når API'en genstartes — også
ved `docker compose up --build`. Det er med vilje, så systemet altid starter
med de samme tre events.
