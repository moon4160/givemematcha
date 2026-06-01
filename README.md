# Marukyu Koyamaen Matcha Restock Watch

This repo checks the Marukyu Koyamaen matcha catalog page on a schedule and saves a snapshot so it can detect when the page changes.

## What it does
- Fetches the matcha catalog page
- Normalizes visible text and links
- Compares the current page hash to the last saved hash
- Optionally posts a Discord alert when the page changes
- Commits the new snapshot back to the repository

## Files
- `check_matcha.py` - the checker script
- `.github/workflows/restock-watch.yml` - scheduled GitHub Actions workflow
- `state/last_hash.txt` - saved hash after the first run
- `state/last_snapshot.txt` - latest normalized snapshot

## Setup
1. Create a GitHub repository.
2. Upload these files.
3. Add a secret named `DISCORD_WEBHOOK_URL` if you want alerts in Discord.
4. Run the workflow manually once.
5. Let the schedule run every 10 minutes.

## Notes
- Marukyu Koyamaen says matcha restocks happen randomly during business hours in Japan time and no restock schedule is announced.
- This checker watches for page changes, which is the simplest free signal.
