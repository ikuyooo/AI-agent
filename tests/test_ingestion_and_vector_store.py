import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.controller import ResearchAgentController
from src.ingestion.chunker import chunk_document
from src.retrieval.vector_store import _legacy_name, _name


class IngestionNameTests(unittest.TestCase):
    def test_chunk_document_uses_uploaded_file_name(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("Abstract\nThis is a test document.")
            path = tmp.name

        try:
            chunks, _ = chunk_document(path, file_name="original-paper.txt")
        finally:
            Path(path).unlink()

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["file_name"], "original-paper.txt")

    def test_controller_does_not_store_temporary_path(self):
        chunks = [{"file_name": "paper.txt", "page": 1}]
        controller = object.__new__(ResearchAgentController)

        with patch("src.core.controller.chunk_document", return_value=(chunks, 0.5)), \
             patch("src.core.controller.add_chunks"), \
             patch("src.core.controller.save_document") as save:
            result = controller.ingest_document("tmp123.txt", file_name="paper.txt")

        self.assertTrue(result["success"])
        save.assert_called_once_with("paper.txt", "", 1, 1, 0.5)


class CollectionNameTests(unittest.TestCase):
    def test_collection_names_do_not_collide_after_sanitizing(self):
        self.assertEqual(_legacy_name("paper.v1.pdf"), _legacy_name("paper_v1.pdf"))
        self.assertNotEqual(_name("paper.v1.pdf"), _name("paper_v1.pdf"))


if __name__ == "__main__":
    unittest.main()
