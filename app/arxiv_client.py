from pathlib import Path
import arxiv


def fetch_papers(query: str, count: int, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    search = arxiv.Search(
        query=query,
        max_results=count,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    paths: list[Path] = []
    client = arxiv.Client(page_size=count, delay_seconds=3, num_retries=3)
    for result in client.results(search):
        slug = result.entry_id.rsplit("/", 1)[-1].replace(".", "_")
        filename = f"{slug}.pdf"
        target = dest_dir / filename
        if not target.exists():
            result.download_pdf(dirpath=str(dest_dir), filename=filename)
        paths.append(target)
    return paths
