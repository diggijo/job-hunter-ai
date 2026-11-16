import time
from pathlib import Path

from app.database import add_lever_board, get_lever_boards
from app.collectors.lever_discovery import validate_lever_token


def import_lever_boards(limit=None):
    file_path = Path("data/lever_companies.tsv")

    existing = {token for token, _ in get_lever_boards()}

    added = 0
    skipped = 0
    invalid = 0

    with file_path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if limit is not None and line_number > limit:
                break

            parts = line.split("\t", 1)

            if len(parts) != 2 or not all(parts):
                raise ValueError(f"Invalid TSV row at line {line_number}")

            board_token, company_name = parts
            board_token = board_token.strip()
            company_name = company_name.strip()

            if not board_token or not company_name:
                raise ValueError(
                    f"Empty token or company at line {line_number}"
                )

            if board_token in existing:
                skipped += 1
                continue

            time.sleep(0.5)
            
            if not validate_lever_token(board_token):
                invalid += 1
                print(f"Invalid or unavailable Lever board: {board_token}")
                continue

            if add_lever_board(board_token, company_name):
                existing.add(board_token)
                added += 1
                print(f"Added: {board_token}", flush=True)
            else:
                skipped += 1

    print("\nLever import complete!")
    print(f"Boards added: {added}")
    print(f"Boards skipped: {skipped}")
    print(f"Invalid/unavailable: {invalid}")
    print(f"Total Lever boards: {len(get_lever_boards())}")


if __name__ == "__main__":
    import_lever_boards()
