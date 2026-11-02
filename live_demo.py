"""Run a short, safe presentation against the locally running lab API."""
import argparse
import sys

import httpx

from app import issue_token


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo against the local MiniBank lab")
    parser.add_argument("--mode", choices=("before", "fixed"), required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    alice = {"Authorization": "Bearer " + issue_token("alice")}
    support = {"Authorization": "Bearer " + issue_token("sam", "support", "admin:users")}
    expected = {"before": (200, 200, 200, False), "fixed": (403, 403, 400, True)}[args.mode]

    try:
        with httpx.Client(base_url=args.url, timeout=5) as client:
            bola = client.get("/accounts/acc-b", headers=alice)
            bfla = client.get("/admin/users", headers=support)
            mass = client.patch("/profile/alice", headers=alice,
                                json={"full_name": "Alice Lab", "role": "admin"})
            transfer_headers = {**alice, "Idempotency-Key": "presentation-001"}
            payload = {"source": "acc-a", "destination": "acc-b", "amount": 10}
            first = client.post("/transfers", headers=transfer_headers, json=payload)
            second = client.post("/transfers", headers=transfer_headers, json=payload)
    except httpx.RequestError as exc:
        print(f"Cannot connect to local API: {exc}")
        return 2

    print(f"\nDEMO DE TAI 27 - {args.mode.upper()} - {args.url}")
    print("Test case                       HTTP   X-Request-ID")
    for label, response in (("BOLA: Alice reads Bob account", bola),
                            ("BFLA: Sam calls admin route", bfla),
                            ("Mass assignment: change role", mass),
                            ("Transfer first request", first),
                            ("Retry same idempotency key", second)):
        print(f"{label:<29} {response.status_code:<6} {response.headers.get('X-Request-ID', '-')}")

    same_transaction = first.status_code == second.status_code == 200 and first.json() == second.json()
    if first.status_code == second.status_code == 200:
        print(f"Transaction IDs: {first.json()['id']} / {second.json()['id']}")
    passed = (bola.status_code, bfla.status_code, mass.status_code, same_transaction) == expected
    print("RESULT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
