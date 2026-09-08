from api.pokemon_api import PokemonAPI

def main():
    api = PokemonAPI()

    print("Testing Pokémon TCG API...")

    sets = api.get_all_sets()

    print(f"Total sets fetched: {len(sets)}")

    if sets:
        first = sets[0]
        print("First set:")
        print(f"Name: {first.get('name')}")
        print(f"ID: {first.get('id')}")
        print(f"Release Date: {first.get('releaseDate')}")

if __name__ == "__main__":
    main()
