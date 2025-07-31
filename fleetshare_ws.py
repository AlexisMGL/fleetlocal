import asyncio
import requests
import websockets
from pymavlink import mavutil
import time

WS_URI        = "ws://127.0.0.1:56781"
HTTP_ENDPOINT = "https://fleetshare.onrender.com/drone-position"
HTTP_ENDPOINT_MISSION = "https://fleetshare.onrender.com/drone-mission"
MIN_INTERVAL  = 2.0  # Intervalle minimum entre les envois en secondes

last_send_time = 0.0
last_lat = None
last_lon = None
last_yaw = None
last_alt = None
last_groundspeed = None
last_airspeed = None
last_alt_vfr = None
last_windspeed = None
last_sysid = None
timestamp = None

mission_expected_count = 0
mission_received_count = 0

# Ajout pour la gestion des waypoints
waypoints = []

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
    global last_send_time, last_lat, last_lon, last_yaw, last_alt, last_groundspeed, last_airspeed, last_sysid, waypoints, last_windspeed, timestamp
    global mission_expected_count, mission_received_count
    async with websockets.connect(WS_URI) as ws:
        print("Connecté au WebSocket MAVLink (binaire).")
        mav = mavutil.mavlink.MAVLink(None)

        while True:
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
                sysid = None
                try:
                    sysid = msg.get_srcSystem()
                except Exception:
                    pass
                if not sysid and hasattr(msg, '_header') and hasattr(msg._header, 'srcSystem'):
                    sysid = msg._header.srcSystem
                if sysid:
                    last_sysid = sysid
                
                # Début de la réception de mission
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_COUNT:
                    mission_expected_count = msg.count
                    mission_received_count = 0
                    waypoints = []
                    print(f"Réception de mission : {mission_expected_count} waypoints attendus.")

                # Réception d'un item de mission
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_ITEM or msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_MISSION_ITEM_INT:
                    if is_waypoint(msg):
                        lat, lon = extract_latlon(msg)
                        if lat is not None and lon is not None:
                            waypoints.append((lat, lon))
                            print(f"Waypoint reçu ({len(waypoints)}) : {lat}, {lon}")
                    mission_received_count += 1  # Incrémenter à chaque item, pas seulement les waypoints

                    # Si tous les items sont reçus, on envoie
                    if mission_expected_count > 0 and mission_received_count == mission_expected_count:
                        wp_str = " ".join([f"WP{i+1}: {lat},{lon}" for i, (lat, lon) in enumerate(waypoints)])
                        payload = {
                            "waypoints": wp_str,
                            "sysid": last_sysid  # Ajout du sysid ici
                        }
                        try:
                            resp = requests.post(
                                HTTP_ENDPOINT_MISSION,
                                json=payload,
                                headers={"User-Agent": "PyFleet/1.0"}
                            )
                            if resp.status_code == 200:
                                print(f"POST WP OK → {wp_str} sysid={last_sysid}")
                            else:
                                print("Erreur HTTP WP :", resp.status_code, resp.text)
                        except Exception as e:
                            print("Exception lors du POST WP :", e)
                        # Reset pour la prochaine mission
                        mission_expected_count = 0
                        mission_received_count = 0
                        waypoints = []
                        
                # GLOBAL_POSITION_INT
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT:
                    last_lat = round(msg.lat * 1e-7, 7)
                    last_lon = round(msg.lon * 1e-7, 7)
                    last_yaw = round(msg.hdg * 0.01, 2)
                    timestamp = int(time.time())

                # VFR_HUD
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD:
                    last_groundspeed = round(msg.groundspeed, 2)
                    last_airspeed = round(msg.airspeed, 2)
                    last_alt = round(msg.alt, 2) 
                   
                if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_WIND:
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
                    last_sysid = msg.get_srcSystem()

                # BATTERY_STATUS
                # if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS:
                #     # On ne prend que Battery Monitor 1 (id=0)
                #     if hasattr(msg, "id") and msg.id == 0:
                #         payload = {
                #             "sysid": last_sysid,
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
            if now - last_send_time >= MIN_INTERVAL and last_lat is not None:
                payload = {
                    "timestamp": timestamp,
                    "lat": last_lat,
                    "lon": last_lon,
                    "yaw": last_yaw,
                    "alt": last_alt,         # Altitude VFR_HUD
                    "groundspeed": last_groundspeed,
                    "airspeed": last_airspeed,
                    "windspeed": last_windspeed, # Vitesse du vent WIND
                    "sysid": last_sysid
                }
                try:
                    resp = requests.post(
                        HTTP_ENDPOINT,
                        json=payload,
                        headers={"User-Agent": "PyFleet/1.0"}
                    )
                    if resp.status_code == 200:
                        print(f"POST OK → timestamp={timestamp} lat={last_lat} lon={last_lon} yaw={last_yaw} alt={last_alt} groundspeed={last_groundspeed} airspeed={last_airspeed} windspeed={last_windspeed} sysid={last_sysid}")
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