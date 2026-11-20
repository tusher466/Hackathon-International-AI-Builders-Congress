"""CLI that calls control API to inject fault."""
from __future__ import annotations

import argparse
import json
import requests


def main():
    parser = argparse.ArgumentParser(description="Inject fault via control API")
    parser.add_argument("--api", default="http://localhost:8000/api/v1/control/inject-fault", help="API URL")
    parser.add_argument("--machine", default="TURBO-01", help="Machine ID")
    parser.add_argument("--type", dest="fault_type", default="degradation", choices=["drift", "spike", "stuck", "degradation", "defect_burst"], help="Fault type")
    parser.add_argument("--magnitude", type=float, default=1.5, help="Magnitude")
    parser.add_argument("--duration", type=int, default=30, help="Duration ticks")
    parser.add_argument("--sensors", nargs="*", help="Target sensors list")
    args = parser.parse_args()

    payload = {
        "machine_id": args.machine,
        "fault_type": args.fault_type,
        "magnitude": args.magnitude,
        "duration_ticks": args.duration,
        "sensors": args.sensors,
    }
    print(f"Injecting fault to {args.api} payload={payload}")
    try:
        resp = requests.post(args.api, json=payload, timeout=10)
        print(f"Status {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print(f"Failed to call API (maybe server not running): {e}")
        print("You can also inject directly via pipeline if running demo script")


if __name__ == "__main__":
    main()
