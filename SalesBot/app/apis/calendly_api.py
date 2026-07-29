import requests
import datetime
import os


from app.config.settings import logger
from datetime import timedelta


def calendly_available_slots_api(tenant_id, slot_datetime):
    # ------------------UNCOMMENT CODE BELOW FOR ACTUAL API USE-------------------------#
    # try:
    #     minutes = slot_datetime.minute
    #     if minutes > 0 and minutes != 30:
    #         minutes_to_add = 30 - (minutes % 30)
    #         rounded_datetime = slot_datetime.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
    #     else:
    #         rounded_datetime = slot_datetime.replace(second=0, microsecond=0)

    #     print("slot_datetime", slot_datetime)

    #     search_start_utc = rounded_datetime
    #     print("search_start_utc", search_start_utc)
    #     search_end_utc = search_start_utc + timedelta(days=7)
    #     search_start_iso = search_start_utc.isoformat(timespec='seconds').replace("+00:00", "Z")
    #     search_end_iso = search_end_utc.isoformat(timespec='seconds').replace("+00:00", "Z")

    #     key = os.getenv("CALENDY_KEY")

    #     headers = {
    #         "Authorization": f"Bearer {key}",
    #         "Content-Type": "application/json"
    #     }

    #     def make_request(url, params=None):
    #         resp = requests.get(url, headers=headers, params=params or {}, timeout=10)
    #         if resp.status_code == 401:
    #             logger.error(f"Calendly 401 - refreshing token for integration")
    #         else:
    #             logger.error("Failed to refresh Calendly token")
    #         return resp

    #     event_types_resp = make_request(
    #         "https://api.calendly.com/event_types",
    #         params={"organization": "https://api.calendly.com/organizations/631cc414-d145-4901-bb06-5cf251ce60a2", "active": True}
    #     )

    #     if not event_types_resp.ok:
    #         logger.error(f"Failed to fetch event types: {event_types_resp.status_code} {event_types_resp.text}")
    #         return {"available": False, "slots": [], "error": "Failed to fetch event types"}

    #     event_types = event_types_resp.json().get("collection", [])
    #     if not event_types:
    #         return {"available": False, "slots": [], "error": "No active event types"}

    #     available_slots = []

    #     for event_type in event_types:
    #         if len(available_slots) >= 5:
    #             break

    #         event_type_uri = event_type["uri"]

    #         slots_resp = make_request(
    #             "https://api.calendly.com/event_type_available_times",
    #             params={
    #                 "event_type": event_type_uri,
    #                 "start_time": search_start_iso,
    #                 "end_time": search_end_iso
    #             }
    #         )

    #         if not slots_resp.ok:
    #             logger.warning(f"Failed to get slots for {event_type['name']}: {slots_resp.text}")
    #             continue

    #         slots = slots_resp.json().get("collection", [])
    #         for slot in slots:
    #             slot_time_str = slot.get("start_time")

    #             slot_utc = datetime.datetime.fromisoformat(slot_time_str.replace("Z", "+00:00"))
    #             slot_local = slot_utc.astimezone(slot_datetime.tzinfo) if slot_datetime.tzinfo else slot_utc

    #             available_slots.append({
    #                 "start_time_utc": slot_time_str,
    # #                 "start_time_local": slot_local.strftime("%Y-%m-%d %H:%M"),
    #                 "status": slot.get("status"),
    #                 "event_type_name": event_type.get("name"),
    #                 "event_type_uri": event_type_uri,
    #                 "event_location_kind": event_type["locations"][0]["kind"],
    #             })

    #             if len(available_slots) >= 5:
    #                 break
    #     if len(available_slots)==0:
    #         return {
    #             "available": False,
    #             "slots": [],
    #             "error": "No available slots"
    #         }

    #     logger.info(f"\n\n\n available_slots : {available_slots} \n\n\n")

    #     return {
    #         "available": len(available_slots) > 0,
    #         "count": len(available_slots),
    #         "slots": available_slots[:5],
    #         "searched_from": search_start_iso,
    #         "searched_to": search_end_iso,
    #         "timezone": str(slot_datetime.tzinfo) if slot_datetime.tzinfo else "UTC"
    #     }

    # except Exception as e:
    #     logger.exception(f"Unexpected error in calendly_available_slots: {str(e)}")
    #     return {"available": False, "slots": [], "error": str(e)}

    # #------------------MOCKED RESPONSE FOR DEMO PURPOSES-------------------------#
    try:
        minutes = slot_datetime.minute
        if minutes > 0 and minutes != 30:
            minutes_to_add = 30 - (minutes % 30)
            rounded_datetime = slot_datetime.replace(second=0, microsecond=0) + timedelta(
                minutes=minutes_to_add
            )
        else:
            rounded_datetime = slot_datetime.replace(second=0, microsecond=0)

        print("slot_datetime", slot_datetime)

        search_start_utc = rounded_datetime
        print("search_start_utc", search_start_utc)
        search_end_utc = search_start_utc + timedelta(days=7)
        search_start_iso = search_start_utc.isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        search_end_iso = search_end_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
        available_slots = [
        # ================== 16 March 2026 (Monday) ==================
        {"start_time_utc": "2026-03-16T05:30:00Z", "start_time_local": "2026-03-16 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-16T07:30:00Z", "start_time_local": "2026-03-16 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-16T10:30:00Z", "start_time_local": "2026-03-16 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-16T11:30:00Z", "start_time_local": "2026-03-16 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-16T13:30:00Z", "start_time_local": "2026-03-16 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 17 March 2026 (Tuesday) ==================
        {"start_time_utc": "2026-03-17T05:30:00Z", "start_time_local": "2026-03-17 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-17T07:30:00Z", "start_time_local": "2026-03-17 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-17T10:30:00Z", "start_time_local": "2026-03-17 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-17T11:30:00Z", "start_time_local": "2026-03-17 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-17T13:30:00Z", "start_time_local": "2026-03-17 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 18 March 2026 (Wednesday) ==================
        {"start_time_utc": "2026-03-18T05:30:00Z", "start_time_local": "2026-03-18 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-18T07:30:00Z", "start_time_local": "2026-03-18 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-18T10:30:00Z", "start_time_local": "2026-03-18 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-18T11:30:00Z", "start_time_local": "2026-03-18 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-18T13:30:00Z", "start_time_local": "2026-03-18 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 19 March 2026 (Thursday) ==================
        {"start_time_utc": "2026-03-19T05:30:00Z", "start_time_local": "2026-03-19 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-19T07:30:00Z", "start_time_local": "2026-03-19 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-19T10:30:00Z", "start_time_local": "2026-03-19 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-19T11:30:00Z", "start_time_local": "2026-03-19 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-19T13:30:00Z", "start_time_local": "2026-03-19 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 20 March 2026 (Friday) ==================
        {"start_time_utc": "2026-03-20T05:30:00Z", "start_time_local": "2026-03-20 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-20T07:30:00Z", "start_time_local": "2026-03-20 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-20T10:30:00Z", "start_time_local": "2026-03-20 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-20T11:30:00Z", "start_time_local": "2026-03-20 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-20T13:30:00Z", "start_time_local": "2026-03-20 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 23 March 2026 (Monday) ==================
        {"start_time_utc": "2026-03-23T05:30:00Z", "start_time_local": "2026-03-23 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-23T07:30:00Z", "start_time_local": "2026-03-23 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-23T10:30:00Z", "start_time_local": "2026-03-23 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-23T11:30:00Z", "start_time_local": "2026-03-23 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-23T13:30:00Z", "start_time_local": "2026-03-23 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 24 March 2026 (Tuesday) ==================
        {"start_time_utc": "2026-03-24T05:30:00Z", "start_time_local": "2026-03-24 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-24T07:30:00Z", "start_time_local": "2026-03-24 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-24T10:30:00Z", "start_time_local": "2026-03-24 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-24T11:30:00Z", "start_time_local": "2026-03-24 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-24T13:30:00Z", "start_time_local": "2026-03-24 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 25 March 2026 (Wednesday) ==================
        {"start_time_utc": "2026-03-25T05:30:00Z", "start_time_local": "2026-03-25 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-25T07:30:00Z", "start_time_local": "2026-03-25 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-25T10:30:00Z", "start_time_local": "2026-03-25 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-25T11:30:00Z", "start_time_local": "2026-03-25 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-25T13:30:00Z", "start_time_local": "2026-03-25 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 26 March 2026 (Thursday) ==================
        {"start_time_utc": "2026-03-26T05:30:00Z", "start_time_local": "2026-03-26 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-26T07:30:00Z", "start_time_local": "2026-03-26 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-26T10:30:00Z", "start_time_local": "2026-03-26 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-26T11:30:00Z", "start_time_local": "2026-03-26 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-26T13:30:00Z", "start_time_local": "2026-03-26 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 27 March 2026 (Friday) ==================
        {"start_time_utc": "2026-03-27T05:30:00Z", "start_time_local": "2026-03-27 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-27T07:30:00Z", "start_time_local": "2026-03-27 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-27T10:30:00Z", "start_time_local": "2026-03-27 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-27T11:30:00Z", "start_time_local": "2026-03-27 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-27T13:30:00Z", "start_time_local": "2026-03-27 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 30 March 2026 (Monday) ==================
        {"start_time_utc": "2026-03-30T05:30:00Z", "start_time_local": "2026-03-30 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-30T07:30:00Z", "start_time_local": "2026-03-30 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-30T10:30:00Z", "start_time_local": "2026-03-30 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-30T11:30:00Z", "start_time_local": "2026-03-30 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-30T13:30:00Z", "start_time_local": "2026-03-30 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},

        # ================== 31 March 2026 (Tuesday) ==================
        {"start_time_utc": "2026-03-31T05:30:00Z", "start_time_local": "2026-03-31 11:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-31T07:30:00Z", "start_time_local": "2026-03-31 13:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-31T10:30:00Z", "start_time_local": "2026-03-31 16:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-31T11:30:00Z", "start_time_local": "2026-03-31 17:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        {"start_time_utc": "2026-03-31T13:30:00Z", "start_time_local": "2026-03-31 19:00", "status": "available", "event_type_name": "30 Minute Meeting", "event_type_uri": "https://api.calendly.com/event_types/1b761a53-2f5c-4958-a782-027e08cb0fe9", "event_location_kind": "google_conference"},
        ]

        return {
            "available": len(available_slots) > 0,
            "count": len(available_slots),
            "slots": available_slots,
            "searched_from": search_start_iso,
            "searched_to": search_end_iso,
            "timezone": str(slot_datetime.tzinfo) if slot_datetime.tzinfo else "UTC",
        }
    except Exception as e:
        logger.error(f"Error in mock calendly_available_slots_api: {e}")
        return {
            "available": False,
            "slots": [],
            "error": str(e)
        }
