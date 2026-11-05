
from pathlib import Path

from app.database import add_ashby_board, get_ashby_boards


def import_ashby_boards():
    file_path = Path("data/ashby_companies.tsv")

    existing = {token for token, _ in get_ashby_boards()}

    added = 0
    skipped = 0

    with file_path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("\t", 1)

            if len(parts) != 2 or not all(parts):
                raise ValueError(f"Invalid TSV row at line {line_number}")

            board_token, company_name = parts
            board_token = board_token.strip()
            company_name = company_name.strip()

            if not board_token or not company_name:
                raise ValueError(f"Empty token or company at line {line_number}")

            if board_token in existing:
                skipped += 1
                continue

            if add_ashby_board(board_token, company_name):
                existing.add(board_token)
                added += 1
            else:
                skipped += 1

    print(f"Boards added: {added}")
    print(f"Boards skipped: {skipped}")
    print(f"Total Ashby boards: {len(get_ashby_boards())}")


if __name__ == "__main__":
    import_ashby_boards()
