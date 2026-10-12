# Server del muro de mensajes: listar y publicar, guardando en Firestore.
import os, uuid
from flask import Flask, request, jsonify
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client(database=os.environ.get("BASE_DATOS", "(default)"))
INSTANCIA = uuid.uuid4().hex[:6]


@app.before_request
def manejar_preflight():
    if request.method == "OPTIONS":
        return "", 204


@app.after_request
def permitir_navegador(respuesta):
    origen = os.environ.get("FRONTEND_URL") or request.headers.get("Origin") or "*"
    respuesta.headers["Access-Control-Allow-Origin"] = origen
    respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return respuesta


@app.get("/")
def salud():
    return "ok"


@app.get("/mensajes")
def listar():
    consulta = (db.collection("mensajes")
                  .order_by("creado", direction=firestore.Query.DESCENDING)
                  .limit(20))
    mensajes = []
    for d in consulta.stream():
        datos = d.to_dict() or {}
        mensajes.append({
            "id": d.id,
            "autor": datos.get("autor", ""),
            "texto": datos.get("texto", ""),
            "likes": datos.get("likes", 0),
        })
    return jsonify(instancia=INSTANCIA, mensajes=mensajes)


@app.post("/mensajes")
def crear():
    datos = request.get_json(silent=True) or {}
    autor = str(datos.get("autor", "")).strip()[:40]
    texto = str(datos.get("texto", "")).strip()[:280]
    if not autor or not texto:
        return jsonify(error="faltan autor o texto"), 400
    db.collection("mensajes").add({
        "autor": autor,
        "texto": texto,
        "creado": firestore.SERVER_TIMESTAMP,
        "likes": 0,
    })
    return jsonify(ok=True, instancia=INSTANCIA), 201


@app.post("/mensajes/<id>/like")
def dar_like(id):
    doc_ref = db.collection("mensajes").document(id)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify(error="mensaje no encontrado"), 404
    doc_ref.update({"likes": firestore.Increment(1)})
    return jsonify(ok=True, instancia=INSTANCIA)

