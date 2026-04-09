from __future__ import annotations

import time


def main() -> None:
    print("RegentOS worker prototype started. Waiting for background governance jobs...")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()

