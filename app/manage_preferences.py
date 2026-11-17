from app.database import (
    get_candidate_profile,
    update_preferred_locations,
)


def manage_preferences():
    while True:
        locations = get_candidate_profile()["preferred_locations"]

        print("\n=== JOB HUNTER AI — LOCATION PREFERENCES ===")

        print("\nCurrent locations:")
        for index, location in enumerate(locations, start=1):
            print(f"{index}. {location}")

        print("\nOptions:")
        print("1. Add a location")
        print("2. Remove a location")
        print("3. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            location = input("Enter location: ").strip()

            if not location:
                print("Location cannot be empty.")
            elif location.casefold() in {
                item.casefold() for item in locations
            }:
                print("Location already exists.")
            else:
                update_preferred_locations(locations + [location])
                print(f"Added: {location}")

        elif choice == "2":
            try:
                number = int(input("Enter location number to remove: "))
                if 1 <= number <= len(locations):
                    removed = locations.pop(number - 1)
                    update_preferred_locations(locations)
                    print(f"Removed: {removed}")
                else:
                    print("Invalid location number.")
            except ValueError:
                print("Please enter a valid number.")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    manage_preferences()
