from __future__ import annotations

import argparse

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a YouTube refresh token for GitHub Actions secrets.")
    parser.add_argument("--client-secrets", default="client_secret.json", help="OAuth desktop client JSON from Google Cloud Console")
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    print("YOUTUBE_REFRESH_TOKEN=" + str(creds.refresh_token))


if __name__ == "__main__":
    main()
