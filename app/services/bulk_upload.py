"""Service for handling bulk uploads of BOM and artwork files."""

import csv
import io
import os
from typing import List, Dict, Tuple, Optional
from fastapi import UploadFile
import re
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


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
    def _find_column(cls, row: Dict, possible_names: List[str]) -> Optional[str]:
        """Find a column value by trying multiple possible names (case-insensitive)."""
        for name in possible_names:
            # Try exact match first
            if name in row and row[name]:
                return row[name]
            # Try case-insensitive match
            for key in row.keys():
                if key.lower() == name.lower() and row[key]:
                    return row[key]
        return None

    @classmethod
    async def parse_bom_file(cls, file: UploadFile) -> Dict:
        """
        Parse BOM file (CSV or Excel) and extract SKU-ingredient mappings.

        Expected columns (flexible names):
        - SKU Code: SKU_Code, sku_code, SKU, sku, Product_Code, product_code, Item, Item Code
        - Ingredient: Ingredient_Name, ingredient_name, Ingredient, ingredient, Name, name, Component, Part
        - Amount: Amount, amount, Quantity, quantity, Qty
        - Source: Source, source, Form, form, Type
        - Unit: Unit, unit
        - CAS: CAS, cas_number, CAS_Number, CAS Number

        Returns dict with:
        - total_rows: int
        - data: List[Dict] of BOM entries
        - columns_found: List[str] of actual column names
        - errors: List[str] of any parsing errors
        """
        content = await file.read()
        filename = file.filename.lower()

        bom_data = []
        columns_found = []
        errors = []

        try:
            # Determine file type and parse accordingly
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                if not OPENPYXL_AVAILABLE:
                    return {
                        'total_rows': 0,
                        'data': [],
                        'columns_found': [],
                        'errors': ['Excel file support requires openpyxl. Please convert to CSV or install openpyxl.']
                    }

                # Parse Excel file
                workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
                sheet = workbook.active

                # Get headers from first row
                headers = []
                for cell in sheet[1]:
                    headers.append(str(cell.value) if cell.value else '')
                columns_found = [h for h in headers if h]

                # Parse data rows
                for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(row):  # Skip empty rows
                        continue

                    row_dict = {}
                    for idx, value in enumerate(row):
                        if idx < len(headers) and headers[idx]:
                            row_dict[headers[idx]] = str(value) if value is not None else ''

                    cls._process_bom_row(row_dict, bom_data, errors, row_idx)

            else:
                # Parse CSV file
                try:
                    decoded = content.decode('utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        decoded = content.decode('latin-1')
                    except UnicodeDecodeError:
                        decoded = content.decode('utf-8', errors='ignore')

                csv_reader = csv.DictReader(io.StringIO(decoded))
                columns_found = list(csv_reader.fieldnames) if csv_reader.fieldnames else []

                for row_idx, row in enumerate(csv_reader, start=2):
                    if not any(row.values()):  # Skip empty rows
                        continue
                    cls._process_bom_row(row, bom_data, errors, row_idx)

            # Add helpful error message if no data was parsed
            if not bom_data and not errors:
                errors.append(
                    f"No valid BOM entries found. Columns detected: {', '.join(columns_found) if columns_found else 'None'}. "
                    f"Please ensure your file has columns for SKU Code and Ingredient Name."
                )

        except Exception as e:
            errors.append(f"Error parsing file: {str(e)}")

        return {
            'total_rows': len(bom_data),
            'data': bom_data,
            'columns_found': columns_found,
            'errors': errors
        }

    @classmethod
    def _process_bom_row(cls, row: Dict, bom_data: List, errors: List, row_num: int):
        """Process a single BOM row and add to bom_data if valid."""
        # Try to extract SKU code from various possible column names
        sku_code = cls._find_column(row, [
            'SKU_Code', 'sku_code', 'SKU', 'sku', 'Product_Code', 'product_code',
            'Item', 'Item Code', 'ItemCode', 'item_code', 'Product', 'product',
            'Product number', 'Product Number', 'PRODUCT NUMBER', 'Product_number',
            'BOM number', 'BOM Number', 'BOM_number', 'bom_number',
            'Product name', 'Product Name', 'PRODUCT NAME', 'Product_name'
        ])

        ingredient_name = cls._find_column(row, [
            'Ingredient_Name', 'ingredient_name', 'Ingredient', 'ingredient',
            'Name', 'name', 'Component', 'component', 'Part', 'part',
            'Material', 'material', 'Item Name', 'Description',
            'Part description', 'Part Description', 'PART DESCRIPTION', 'Part_description',
            'Part No.', 'Part No', 'Part_No', 'PartNo', 'Part Number', 'Part_Number',
            'Component Name', 'Component Description', 'Material Name',
            'BOM name', 'BOM Name', 'BOM_name', 'bom_name'
        ])

        if sku_code and ingredient_name:
            amount = cls._find_column(row, [
                'Amount', 'amount', 'Quantity', 'quantity', 'Qty', 'qty', 'Weight', 'weight',
                'QTY', 'QUANTITY', 'Amount Required', 'Required Quantity'
            ]) or ''

            source = cls._find_column(row, [
                'Source', 'source', 'Form', 'form', 'Type', 'type', 'Origin', 'origin',
                'Supplier', 'supplier', 'Vendor', 'vendor', 'Manufacturer'
            ]) or ''

            unit = cls._find_column(row, [
                'Unit', 'unit', 'UOM', 'uom', 'Units', 'units',
                'Unit of measurement', 'Unit_of_measurement', 'Measurement Unit'
            ]) or ''

            cas_number = cls._find_column(row, [
                'CAS', 'cas_number', 'CAS_Number', 'CAS Number', 'CAS#', 'cas'
            ]) or ''

            bom_data.append({
                'sku_code': sku_code.strip(),
                'ingredient_name': ingredient_name.strip(),
                'amount': amount.strip() if amount else '',
                'source': source.strip() if source else '',
                'unit': unit.strip() if unit else '',
                'cas_number': cas_number.strip() if cas_number else '',
                'row_number': row_num
            })
        elif sku_code or ingredient_name:
            # One column found but not the other
            missing = 'Ingredient Name' if sku_code else 'SKU Code'
            errors.append(f"Row {row_num}: Missing {missing}")

    @classmethod
    async def parse_bom_csv(cls, file: UploadFile) -> List[Dict]:
        """
        Legacy method for backward compatibility.
        Use parse_bom_file() for better error handling.
        """
        result = await cls.parse_bom_file(file)
        return result['data']

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
