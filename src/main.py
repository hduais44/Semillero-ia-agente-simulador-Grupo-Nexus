import json
import random
import time


def cargar_configuracion(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def generar_mensaje(config):
    frases = {
        "enojado": {
            "reclamo de factura": [
                "Estoy muy molesto por el cobro incorrecto.",
                "Esto es inaceptable, quiero una solución ya.",
                "Mi factura está mal y nadie me ayuda."
            ]
        },
        "calmado": {
            "consulta de servicio": [
                "Hola, quisiera información sobre el servicio.",
                "Podrían indicarme cómo funciona el plan.",
                "Tengo una consulta, por favor."
            ]
        }
    }

    tipo = config["tipo_cliente"]
    objetivo = config["objetivo_conversacion"]

    return random.choice(frases.get(tipo, {}).get(objetivo, ["Hola"]))


def responder_bot(mensaje_cliente):
    respuestas = [
        "Gracias por contactarnos, estamos revisando su caso.",
        "Entendemos su situación, permítanos ayudarle.",
        "Estamos procesando su solicitud."
    ]
    return random.choice(respuestas)


def ejecutar_agente():
    config = cargar_configuracion("src/config/cliente.json")

    paciencia = config["nivel_paciencia"]
    max_interacciones = config["max_interacciones"]
    interacciones = 0

    print("\n🤖 Agente Simulador de Clientes iniciado\n")

    while interacciones < max_interacciones and paciencia > 0:
        mensaje_cliente = generar_mensaje(config)
        print(f"🧑 Cliente: {mensaje_cliente}")

        respuesta = responder_bot(mensaje_cliente)
        time.sleep(1)
        print(f"🤖 Bot: {respuesta}\n")

        paciencia -= 1
        interacciones += 1

    print("🔚 Conversación finalizada")


if __name__ == "__main__":
    ejecutar_agente()
