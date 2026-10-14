from app.database import get_greenhouse_boards

boards = get_greenhouse_boards()

print(f"Total Greenhouse boards: {len(boards)}")

for board in boards:
    print(board)