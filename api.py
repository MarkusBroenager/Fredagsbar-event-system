import time

from flask import Flask, request

app = Flask(__name__)

events = [
    {
        "id": 1,
        "title": "Quizaften",
        "date": "2026-11-13",
        "capacity": 3,
        "participants": ["Anna", "Bo"],
    },
    {
        "id": 2,
        "title": "Brætspilsaften",
        "date": "2026-11-20",
        "capacity": 5,
        "participants": ["Clara"],
    },
    {
        "id": 3,
        "title": "Beerpong-turnering",
        "date": "2026-11-27",
        "capacity": 2,
        "participants": ["David", "Emma"],
    },
]
naeste_id = 4


def find_event(event_id):
    for event in events:
        if event["id"] == event_id:
            return event
    return None


def er_positivt_heltal(vaerdi):
    if isinstance(vaerdi, bool):
        return False
    return isinstance(vaerdi, int) and vaerdi >= 1


@app.get("/events")
def hent_events():
    return events, 200


@app.get("/events/<int:event_id>")
def hent_event(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event {event_id} findes ikke"}, 404
    return event, 200


@app.post("/events")
def opret_event():
    global naeste_id

    data = request.get_json(silent=True) or {}

    titel = data.get("title")
    dato = data.get("date")
    pladser = data.get("capacity")

    if not titel or not dato:
        return {"error": "title og date skal udfyldes"}, 400

    if not er_positivt_heltal(pladser):
        return {"error": "capacity skal være et positivt heltal"}, 400

    event = {
        "id": naeste_id,
        "title": titel,
        "date": dato,
        "capacity": pladser,
        "participants": [],
    }
    naeste_id += 1
    events.append(event)
    return event, 201


@app.post("/events/<int:event_id>/signups")
def tilmeld(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event {event_id} findes ikke"}, 404

    data = request.get_json(silent=True) or {}
    navn = data.get("name")

    if not navn:
        return {"error": "name mangler"}, 400

    if navn in event["participants"]:
        return {"error": f"{navn} er allerede tilmeldt {event['title']}"}, 409

    if len(event["participants"]) >= event["capacity"]:
        return {"error": f"{event['title']} er fuldt"}, 409

    event["participants"].append(navn)
    return event, 201


@app.delete("/events/<int:event_id>/signups/<name>")
def afmeld(event_id, name):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event {event_id} findes ikke"}, 404

    if name not in event["participants"]:
        return {"error": f"{name} er ikke tilmeldt {event['title']}"}, 404

    event["participants"].remove(name)
    return "", 204


@app.delete("/events/<int:event_id>")
def slet_event(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event {event_id} findes ikke"}, 404

    events.remove(event)
    return "", 204


@app.get("/debug/slow")
def langsom():
    """Svarer med vilje for langsomt, så frontendens timeout kan afprøves.

    Ligger under /debug/ og ikke /events/, så den ikke forveksles med en
    rigtig rute.
    """
    time.sleep(5)
    return {"besked": "Dette svar var fem sekunder undervejs"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
