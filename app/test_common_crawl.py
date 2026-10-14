import httpx


def test_common_crawl():
    indexes_response = httpx.get(
        "https://index.commoncrawl.org/collinfo.json",
        timeout=20.0
    )
    indexes_response.raise_for_status()

    latest_index = indexes_response.json()[0]
    index_url = latest_index["cdx-api"]

    print(f"Searching index: {latest_index['id']}")

    params = {
        "url": "boards.greenhouse.io/neo4j",
        "output": "json",
        "filter": "status:200",
        "collapse": "urlkey"
    }

    try:
        response = httpx.get(
            index_url,
            params=params,
            timeout=60.0
        )
        response.raise_for_status()

        lines = response.text.strip().splitlines()

        print(f"Greenhouse URLs found: {len(lines)}")

        for line in lines[:10]:
            print(httpx.Response(200, text=line).json().get("url"))

    except httpx.HTTPError as error:
        print(f"Common Crawl search failed: {error}")


if __name__ == "__main__":
    test_common_crawl()