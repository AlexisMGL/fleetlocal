"""
Ce script se connecte à un flux MAVLink via WebSocket et transmet périodiquement
les données au serveur FleetShare.
Créateur : AlexisMGL
Dernière modification : 31 juillet 2025
"""

import asyncio
import requests
import websockets
from pymavlink import mavutil
import time
import subprocess

WS_URI        = "ws://127.0.0.1:56781"
HTTP_ENDPOINT = "https://fleetshare.onrender.com/drone-position"
HTTP_ENDPOINT_MISSION = "https://fleetshare.onrender.com/drone-mission"
MIN_INTERVAL  = 2.0  # Intervalle minimum entre les envois en secondes

REQUIRED_PROCESSES = (
    "MissionPlanner.exe",
    "GCSAM.exe",
)
PROCESS_CHECK_INTERVAL = 10  # seconds between process checks
CREATE_NO_WINDOW = 0x08000000

last_send_time = 0.0
last_lat = None
last_lon = None
last_yaw = None
last_alt = None
last_groundspeed = None
last_airspeed = None
last_alt_vfr = None
last_windspeed = None
last_position_sysid = None
last_mission_sysid = None
timestamp = None

mission_expected_count = 0
mission_received_count = 0

# Ajout pour la gestion des waypoints
waypoints = []


def is_process_running(process_name):
    """Return True if the given Windows process is running."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
    except Exception as exc:
        print(f"Unable to check process {process_name}: {exc}")
        return False
    target = process_name.lower()
    for line in result.stdout.splitlines():
        if line.lower().startswith(target):
            return True
    return False


def has_required_process_running():
    return any(is_process_running(name) for name in REQUIRED_PROCESSES)


async def wait_for_required_process():
    waited = False
    while not has_required_process_running():
        if not waited:
            print(f"En attente de MissionPlanner.exe ou GCSAM.exe... nouvelle verification dans {PROCESS_CHECK_INTERVAL}s.")
        else:
            print(f"Toujours en attente... prochaine verification dans {PROCESS_CHECK_INTERVAL}s.")
        waited = True
        await asyncio.sleep(PROCESS_CHECK_INTERVAL)
    if waited:
        print("Processus requis detecte, demarrage du streaming.")


def is_waypoint(msg):
    # MAV_CMD_NAV_WAYPOINT = 16
    return hasattr(msg, "command") and msg.command == 16

def extract_latlon(msg):
    if hasattr(msg, "x") and hasattr(msg, "y"):
        # MISSION_ITEM (float lat/lon)
        return round(msg.x, 7), round(msg.y, 7)
    elif hasattr(msg, "param5") and hasattr(msg, "param6"):
        # MISSION_ITEM_INT (int32 lat/lon * 1e7)
        return round(msg.param5 * 1e-7, 7), round(msg.param6 * 1e-7, 7)
    return None, None

async def stream_positions():
    global last_send_time, last_lat, last_lon, last_yaw, last_alt, last_groundspeed, last_airspeed, last_position_sysid, waypoints, last_windspeed, timestamp
    global mission_expected_count, mission_received_count, last_mission_sysid

    await wait_for_required_process()

    async with websockets.connect(WS_URI) as ws:
        print("Connecté au WebSocket MAVLink (binaire).")
        mav = mavutil.mavlink.MAVLink(None)

        while True:
            if not has_required_process_running():
                print("Processus requis absent. Suspension du streaming.")
                break

            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:

                continue
            except websockets.ConnectionClosed:
                print("WebSocket fermé, tentative de reconnexion...")
                break

            if isinstance(raw, str):
                continue

            buf = bytearray(raw)
            for b in buf:
                msg = mav.parse_char(bytes([b]))
                if not msg:
                    continue

                    # Récupération robuste du sysid
                msg_sysid = None
                try:
                    msg_sysid = msg.get_srcSystem()
                except Exception:
                    pass
                if msg_sysid is None and hasattr(msg, '_header') and hasattr(msg._header, 'srcSystem'):
                    msg_sysid = msg._header.srcSystem
                
                # Début de la réception de mission
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_COUNT:
                    mission_expected_count = msg.count
                    mission_received_count = 0
                    waypoints = []
                    if msg_sysid is not None:
                        last_mission_sysid = msg_sysid
                    print(f"Réception de mission : {mission_expected_count} waypoints attendus.")

                # Réception d'un item de mission
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_ITEM or msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_ITEM_INT:
                    if is_waypoint(msg):
                        lat, lon = extract_latlon(msg)
                        if lat is not None and lon is not None:
                            waypoints.append((lat, lon))
                            print(f"Waypoint reçu ({len(waypoints)}) : {lat}, {lon}")
                    mission_received_count += 1  # Incrémenter à chaque item, pas seulement les waypoints
                    if msg_sysid is not None:
                        last_mission_sysid = msg_sysid

                    # Si tous les items sont reçus, on envoie
                    if mission_expected_count > 0 and mission_received_count == mission_expected_count:
                        wp_str = " ".join([f"WP{i+1}: {lat},{lon}" for i, (lat, lon) in enumerate(waypoints)])
                        mission_sysid = last_mission_sysid or last_position_sysid
                        if mission_sysid is None:
                            print("Impossible d'envoyer la mission : sysid inconnu.")
                        else:
                            payload = {
                                "waypoints": wp_str,
                                "sysid": mission_sysid  # Ajout du sysid ici
                            }
                            try:
                                resp = requests.post(
                                    HTTP_ENDPOINT_MISSION,
                                    json=payload,
                                    headers={"User-Agent": "PyFleet/1.0"}
                                )
                                if resp.status_code == 200:
                                    print(f"POST WP OK → {wp_str} sysid={mission_sysid}")
                                else:
                                    print("Erreur HTTP WP :", resp.status_code, resp.text)
                            except Exception as e:
                                print("Exception lors du POST WP :", e)
                        # Reset pour la prochaine mission
                        mission_expected_count = 0
                        mission_received_count = 0
                        waypoints = []
                        last_mission_sysid = None

                # GLOBAL_POSITION_INT
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT:
                    last_lat = round(msg.lat * 1e-7, 7)
                    last_lon = round(msg.lon * 1e-7, 7)
                    last_yaw = round(msg.hdg * 0.01, 2)
                    timestamp = int(time.time())
                    if msg_sysid is not None:
                        last_position_sysid = msg_sysid

                # VFR_HUD
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD:
                    if last_position_sysid is None or msg_sysid == last_position_sysid:
                        last_groundspeed = round(msg.groundspeed, 2)
                        last_airspeed = round(msg.airspeed, 2)
                        last_alt = round(msg.alt, 2)

                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_WIND:
                    if last_position_sysid is None or msg_sysid == last_position_sysid:
                        last_windspeed = round(msg.speed, 2)

                # HIGH_LATENCY2
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_HIGH_LATENCY2:
                    # lat/lon en degrés, alt en mètres, vitesse en m/s, heading en degrés
                    last_lat = round(msg.latitude, 7)
                    last_lon = round(msg.longitude, 7)
                    last_alt = msg.altitude
                    last_groundspeed = round(msg.groundspeed, 2)
                    last_airspeed = round(msg.airspeed, 2)
                    last_yaw = msg.heading
                    if msg_sysid is not None:
                        last_position_sysid = msg_sysid
                    timestamp = int(time.time())

                # BATTERY_STATUS
                # if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS:
                #     # On ne prend que Battery Monitor 1 (id=0)
                #     if hasattr(msg, "id") and msg.id == 0:
                #         payload = {
                #             "sysid": last_position_sysid,
                #             "battery_id": msg.id,
                #             "voltage": [v for v in msg.voltages if v != 65535],  # 65535 = valeur non utilisée
                #             "current_battery": msg.current_battery,  # en 10 mA
                #             "battery_remaining": msg.battery_remaining,  # en %
                #             "temperature": msg.temperature  # en cdegC
                #         }
                #         try:
                #             resp = requests.post(
                #                 "https://fleetshare.onrender.com/battery",
                #                 json=payload,
                #                 headers={"User-Agent": "PyFleet/1.0"}
                #             )
                #             if resp.status_code == 200:
                #                 print(f"POST BATTERY OK → {payload}")
                #             else:
                #                 print("Erreur HTTP BATTERY :", resp.status_code, resp.text)
                #         except Exception as e:
                #             print("Exception lors du POST BATTERY :", e)
            now = asyncio.get_event_loop().time()
            if now - last_send_time >= MIN_INTERVAL and last_lat is not None and last_position_sysid is not None:
                payload = {
                    "timestamp": timestamp,
                    "lat": last_lat,
                    "lon": last_lon,
                    "yaw": last_yaw,
                    "alt": last_alt,         # Altitude VFR_HUD
                    "groundspeed": last_groundspeed,
                    "airspeed": last_airspeed,
                    "windspeed": last_windspeed, # Vitesse du vent WIND
                    "sysid": last_position_sysid
                }
                try:
                    resp = requests.post(
                        HTTP_ENDPOINT,
                        json=payload,
                        headers={"User-Agent": "PyFleet/1.0"}
                    )
                    if resp.status_code == 200:
                        print(f"POST OK → timestamp={timestamp} lat={last_lat} lon={last_lon} yaw={last_yaw} alt={last_alt} groundspeed={last_groundspeed} airspeed={last_airspeed} windspeed={last_windspeed} sysid={last_position_sysid}")
                    else:
                        print("Erreur HTTP :", resp.status_code, resp.text)
                except Exception as e:
                    print("Exception lors du POST :", e)
                last_send_time = now

async def main():
    while True:
        try:
            await stream_positions()
        except Exception as e:
            print("Erreur de connexion ou autre :", e)
        print("Nouvelle tentative de connexion dans 3 secondes...")
        await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur.")