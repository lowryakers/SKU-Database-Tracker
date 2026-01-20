"""Service for handling bulk uploads of BOM and artwork files."""

import csv
import io
import os
from typing import List, Dict, Tuple, Optional
from fastapi import UploadFile
import re


class BulkUploadService:
    """Service for bulk uploading and matching BOM/artwork files to SKUs."""

    UPLOAD_DIR = "/tmp/sku_uploads"
    BOM_DIR = f"{UPLOAD_DIR}/bom"
    ARTWORK_DIR = f"{UPLOAD_DIR}/artwork"

    @classmethod
    def _ensure_dirs(cls):
        """Ensure upload directories exist."""
        os.makedirs(cls.BOM_DIR, exist_ok=True)
        os.makedirs(cls.ARTWORK_DIR, exist_ok=True)

    @classmethod
    async def parse_bom_csv(cls, file: UploadFile) -> List[Dict]:
        """
        Parse BOM CSV file and extract SKU-ingredient mappings.

        Expected CSV format:
        SKU_Code, Ingredient_Name, Amount, Source, ...

        Returns list of BOM entries with auto-matching suggestions.
        """
        content = await file.read()
        decoded = content.decode('utf-8-sig')  # Handle BOM in CSV

        bom_data = []
        csv_reader = csv.DictReader(io.StringIO(decoded))

        for row in csv_reader:
            # Try to extract SKU code from various possible column names
            sku_code = (
                row.get('SKU_Code') or
                row.get('sku_code') or
                row.get('SKU') or
                row.get('sku') or
                row.get('Product_Code') or
                row.get('product_code')
            )

            ingredient_name = (
                row.get('Ingredient_Name') or
                row.get('ingredient_name') or
                row.get('Ingredient') or
                row.get('ingredient') or
                row.get('Name') or
                row.get('name')
            )

            if sku_code and ingredient_name:
                bom_data.append({
                    'sku_code': sku_code.strip(),
                    'ingredient_name': ingredient_name.strip(),
                    'amount': row.get('Amount') or row.get('amount') or row.get('Quantity') or '',
                    'source': row.get('Source') or row.get('source') or row.get('Form') or '',
                    'unit': row.get('Unit') or row.get('unit') or '',
                    'cas_number': row.get('CAS') or row.get('cas_number') or row.get('CAS_Number') or '',
                    'raw_row': row  # Keep original data
                })

        return bom_data

    @classmethod
    async def save_bom_file(cls, file: UploadFile, sku_code: str) -> str:
        """
        Save BOM file to filesystem.

        Returns the file path.
        """
        cls._ensure_dirs()

        # Sanitize filename
        safe_sku_code = re.sub(r'[^a-zA-Z0-9_-]', '_', sku_code)
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{safe_sku_code}_bom{file_extension}"
        filepath = os.path.join(cls.BOM_DIR, filename)

        # Save file
        content = await file.read()
        with open(filepath, 'wb') as f:
            f.write(content)

        return filepath

    @classmethod
    async def save_artwork_file(cls, file: UploadFile, sku_code: str) -> str:
        """
        Save artwork file to filesystem.

        Returns the file path.
        """
        cls._ensure_dirs()

        # Sanitize filename
        safe_sku_code = re.sub(r'[^a-zA-Z0-9_-]', '_', sku_code)
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{safe_sku_code}_artwork{file_extension}"
        filepath = os.path.join(cls.ARTWORK_DIR, filename)

        # Save file
        content = await file.read()
        with open(filepath, 'wb') as f:
            f.write(content)

        return filepath

    @classmethod
    def match_files_to_skus(cls, files: List[UploadFile], available_sku_codes: List[str]) -> List[Dict]:
        """
        Auto-match uploaded files to SKUs based on filename patterns.

        Returns list of matches with confidence scores.
        """
        matches = []

        for file in files:
            filename = file.filename
            best_match = None
            best_score = 0

            for sku_code in available_sku_codes:
                # Calculate match score
                score = 0

                # Exact match in filename
                if sku_code.lower() in filename.lower():
                    score = 100

                # Partial match
                elif any(part in filename.lower() for part in sku_code.lower().split('-')):
                    score = 70

                # Match without special characters
                clean_sku = re.sub(r'[^a-zA-Z0-9]', '', sku_code.lower())
                clean_filename = re.sub(r'[^a-zA-Z0-9]', '', filename.lower())
                if clean_sku in clean_filename:
                    score = max(score, 80)

                if score > best_score:
                    best_score = score
                    best_match = sku_code

            matches.append({
                'filename': filename,
                'suggested_sku': best_match,
                'confidence': best_score,
                'file': file
            })

        return matches

    @classmethod
    async def bulk_upload_artworks(
        cls,
        files: List[UploadFile],
        sku_mappings: Dict[str, str]  # filename -> sku_code mapping
    ) -> List[Dict]:
        """
        Bulk upload artwork files with manual SKU mappings.

        Returns list of uploaded files with their paths.
        """
        results = []

        for file in files:
            sku_code = sku_mappings.get(file.filename)

            if sku_code:
                try:
                    filepath = await cls.save_artwork_file(file, sku_code)
                    results.append({
                        'filename': file.filename,
                        'sku_code': sku_code,
                        'filepath': filepath,
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'sku_code': sku_code,
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                results.append({
                    'filename': file.filename,
                    'status': 'skipped',
                    'error': 'No SKU mapping provided'
                })

        return results

    @classmethod
    async def bulk_upload_boms(
        cls,
        files: List[UploadFile],
        sku_mappings: Dict[str, str]  # filename -> sku_code mapping
    ) -> List[Dict]:
        """
        Bulk upload BOM files with manual SKU mappings.

        Returns list of uploaded files with their paths.
        """
        results = []

        for file in files:
            sku_code = sku_mappings.get(file.filename)

            if sku_code:
                try:
                    filepath = await cls.save_bom_file(file, sku_code)

                    # Also parse the CSV to extract ingredients
                    await file.seek(0)  # Reset file pointer
                    bom_data = await cls.parse_bom_csv(file)

                    results.append({
                        'filename': file.filename,
                        'sku_code': sku_code,
                        'filepath': filepath,
                        'ingredients_count': len(bom_data),
                        'ingredients': bom_data,
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'sku_code': sku_code,
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                results.append({
                    'filename': file.filename,
                    'status': 'skipped',
                    'error': 'No SKU mapping provided'
                })

        return results
