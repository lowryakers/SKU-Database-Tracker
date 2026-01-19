"""Export service for generating Excel, PDF, and CSV files."""

import csv
import io
from datetime import datetime
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas

from app.models.sku import SKU


class ExportService:
    """Service for exporting SKU data to various formats."""

    @staticmethod
    def export_to_excel(
        skus: List[SKU],
        include_ingredients: bool = True,
        include_internal_notes: bool = False
    ) -> bytes:
        """
        Export SKUs to Excel format with NSF certification fields.

        Args:
            skus: List of SKU objects to export
            include_ingredients: Include ingredient details
            include_internal_notes: Include internal notes

        Returns:
            Excel file as bytes
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "SKU Data"

        # Define headers based on NSF requirements
        headers = [
            "SKU Code", "Product Name", "Brand Name", "Product Type", "Category",
            "Description", "Net Content", "Serving Size", "Servings/Container",
            "Quantity in Stock", "Unit Price", "Storage Location",
            # Manufacturing
            "Manufacturer Name", "Manufacturing Facility", "Facility Address",
            "City", "State/Province", "Country", "Facility ID",
            # Batch/Lot
            "Lot Number", "Batch Number", "Manufacturing Date", "Expiration Date",
            # Supplier
            "Supplier Name", "Supplier Contact", "Supplier Email", "Supplier Phone",
            # NSF Certification
            "NSF Certification Type", "NSF Status", "NSF Cert Number",
            "NSF Cert Date", "NSF Expiration Date", "Next Audit Date",
            "Last Test Date", "Banned Substances Tested", "Test Results",
            # Label & Claims
            "Label Claims", "Intended Use", "Directions for Use", "Warnings",
            "Allergens", "Formulation Details",
            # Documentation
            "SDS Document URL", "COA Document URL", "Label Image URL",
            # Contact
            "Primary Contact Name", "Primary Contact Email", "Primary Contact Phone",
            # Status
            "Active", "Requires NSF Certification", "Notes",
        ]

        if include_internal_notes:
            headers.append("Internal Notes")

        # Style the header row
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Add data rows
        for row_num, sku in enumerate(skus, 2):
            data_row = [
                sku.sku_code,
                sku.name,
                sku.brand_name,
                sku.product_type,
                sku.category,
                sku.description,
                sku.net_content,
                sku.serving_size,
                sku.servings_per_container,
                sku.quantity,
                sku.unit_price,
                sku.storage_location,
                # Manufacturing
                sku.manufacturer_name,
                sku.manufacturer_facility,
                sku.manufacturer_address,
                sku.manufacturer_city,
                sku.manufacturer_state,
                sku.manufacturer_country,
                sku.manufacturer_facility_id,
                # Batch/Lot
                sku.lot_number,
                sku.batch_number,
                sku.manufacturing_date.isoformat() if sku.manufacturing_date else None,
                sku.expiration_date.isoformat() if sku.expiration_date else None,
                # Supplier
                sku.supplier_name,
                sku.supplier_contact,
                sku.supplier_email,
                sku.supplier_phone,
                # NSF
                sku.nsf_certification_type,
                sku.nsf_certification_status,
                sku.nsf_certification_number,
                sku.nsf_certification_date.isoformat() if sku.nsf_certification_date else None,
                sku.nsf_expiration_date.isoformat() if sku.nsf_expiration_date else None,
                sku.nsf_next_audit_date.isoformat() if sku.nsf_next_audit_date else None,
                sku.nsf_last_test_date.isoformat() if sku.nsf_last_test_date else None,
                "Yes" if sku.nsf_banned_substances_tested else "No",
                sku.nsf_test_results,
                # Label
                sku.label_claims,
                sku.intended_use,
                sku.directions_for_use,
                sku.warnings,
                sku.allergens,
                sku.formulation_details,
                # Docs
                sku.sds_document_url,
                sku.coa_document_url,
                sku.label_image_url,
                # Contact
                sku.primary_contact_name,
                sku.primary_contact_email,
                sku.primary_contact_phone,
                # Status
                "Yes" if sku.is_active else "No",
                "Yes" if sku.requires_nsf_certification else "No",
                sku.notes,
            ]

            if include_internal_notes:
                data_row.append(sku.internal_notes)

            for col_num, value in enumerate(data_row, 1):
                ws.cell(row=row_num, column=col_num, value=value)

        # Auto-adjust column widths
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 20

        # Create ingredients sheet if requested
        if include_ingredients:
            ws_ing = wb.create_sheet(title="Ingredients")
            ing_headers = [
                "SKU Code", "Product Name", "Ingredient Name", "Amount",
                "Unit", "Source", "% Daily Value", "Supplier", "CAS Number",
                "Active Ingredient", "Allergen", "Display Order"
            ]

            # Style headers
            for col_num, header in enumerate(ing_headers, 1):
                cell = ws_ing.cell(row=1, column=col_num, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Add ingredient data
            ing_row = 2
            for sku in skus:
                if sku.ingredients_list:
                    for ing in sku.ingredients_list:
                        ws_ing.cell(row=ing_row, column=1, value=sku.sku_code)
                        ws_ing.cell(row=ing_row, column=2, value=sku.name)
                        ws_ing.cell(row=ing_row, column=3, value=ing.name)
                        ws_ing.cell(row=ing_row, column=4, value=ing.amount)
                        ws_ing.cell(row=ing_row, column=5, value=ing.unit)
                        ws_ing.cell(row=ing_row, column=6, value=ing.source)
                        ws_ing.cell(row=ing_row, column=7, value=ing.percent_daily_value)
                        ws_ing.cell(row=ing_row, column=8, value=ing.ingredient_supplier)
                        ws_ing.cell(row=ing_row, column=9, value=ing.cas_number)
                        ws_ing.cell(row=ing_row, column=10, value="Yes" if ing.is_active_ingredient else "No")
                        ws_ing.cell(row=ing_row, column=11, value="Yes" if ing.is_allergen else "No")
                        ws_ing.cell(row=ing_row, column=12, value=ing.display_order)
                        ing_row += 1

            # Auto-adjust ingredient column widths
            for col in range(1, len(ing_headers) + 1):
                ws_ing.column_dimensions[get_column_letter(col)].width = 18

        # Save to bytes
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        return excel_file.getvalue()

    @staticmethod
    def export_to_pdf(
        skus: List[SKU],
        include_ingredients: bool = True,
        include_internal_notes: bool = False,
        title: str = "SKU Database - NSF Certification Report"
    ) -> bytes:
        """
        Export SKUs to PDF format.

        Args:
            skus: List of SKU objects to export
            include_ingredients: Include ingredient details
            include_internal_notes: Include internal notes
            title: Document title

        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )

        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#366092'),
            spaceAfter=12,
            alignment=1  # Center
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))

        # Process each SKU
        for sku in skus:
            # SKU Header
            sku_header_style = ParagraphStyle(
                'SKUHeader',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#366092'),
                spaceAfter=6
            )
            elements.append(Paragraph(f"SKU: {sku.sku_code} - {sku.name}", sku_header_style))

            # Basic Information Table
            basic_data = [
                ["Field", "Value"],
                ["Brand Name", sku.brand_name or ""],
                ["Product Type", sku.product_type or ""],
                ["Category", sku.category or ""],
                ["Net Content", sku.net_content or ""],
                ["Quantity in Stock", str(sku.quantity)],
            ]

            # Manufacturing Information
            if sku.manufacturer_name:
                mfg_data = [
                    ["Manufacturing Information", ""],
                    ["Manufacturer", sku.manufacturer_name or ""],
                    ["Facility", sku.manufacturer_facility or ""],
                    ["Location", f"{sku.manufacturer_city or ''}, {sku.manufacturer_state or ''}, {sku.manufacturer_country or ''}"],
                    ["Lot Number", sku.lot_number or ""],
                    ["Manufacturing Date", sku.manufacturing_date.isoformat() if sku.manufacturing_date else ""],
                    ["Expiration Date", sku.expiration_date.isoformat() if sku.expiration_date else ""],
                ]
                basic_data.extend(mfg_data)

            # NSF Certification Information
            if sku.nsf_certification_type:
                nsf_data = [
                    ["NSF Certification", ""],
                    ["Certification Type", sku.nsf_certification_type or ""],
                    ["Status", sku.nsf_certification_status or ""],
                    ["Cert Number", sku.nsf_certification_number or ""],
                    ["Cert Date", sku.nsf_certification_date.isoformat() if sku.nsf_certification_date else ""],
                    ["Expiration", sku.nsf_expiration_date.isoformat() if sku.nsf_expiration_date else ""],
                    ["Banned Substances Tested", "Yes" if sku.nsf_banned_substances_tested else "No"],
                ]
                basic_data.extend(nsf_data)

            table = Table(basic_data, colWidths=[2.5*inch, 5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))

            # Ingredients
            if include_ingredients and sku.ingredients_list:
                elements.append(Paragraph("Ingredients:", styles['Heading3']))
                ing_data = [["Name", "Amount", "Source", "% DV"]]
                for ing in sorted(sku.ingredients_list, key=lambda x: x.display_order):
                    ing_data.append([
                        ing.name,
                        ing.amount or "",
                        ing.source or "",
                        ing.percent_daily_value or ""
                    ])

                ing_table = Table(ing_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1*inch])
                ing_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(ing_table)
                elements.append(Spacer(1, 0.2*inch))

            elements.append(PageBreak())

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def export_to_csv(
        skus: List[SKU],
        include_internal_notes: bool = False
    ) -> str:
        """
        Export SKUs to CSV format.

        Args:
            skus: List of SKU objects to export
            include_internal_notes: Include internal notes

        Returns:
            CSV data as string
        """
        output = io.StringIO()
        headers = [
            "SKU Code", "Product Name", "Brand Name", "Product Type", "Category",
            "Description", "Net Content", "Serving Size", "Servings/Container",
            "Quantity", "Unit Price", "Storage Location",
            "Manufacturer Name", "Manufacturing Facility", "Facility Address",
            "City", "State", "Country", "Facility ID",
            "Lot Number", "Batch Number", "Manufacturing Date", "Expiration Date",
            "Supplier Name", "Supplier Contact", "Supplier Email", "Supplier Phone",
            "NSF Certification Type", "NSF Status", "NSF Cert Number",
            "NSF Cert Date", "NSF Expiration", "Next Audit", "Last Test Date",
            "Banned Substances Tested", "Test Results",
            "Label Claims", "Intended Use", "Directions", "Warnings", "Allergens",
            "SDS URL", "COA URL", "Label Image URL",
            "Primary Contact Name", "Primary Contact Email", "Primary Contact Phone",
            "Active", "Requires NSF Cert", "Notes"
        ]

        if include_internal_notes:
            headers.append("Internal Notes")

        writer = csv.writer(output)
        writer.writerow(headers)

        for sku in skus:
            row = [
                sku.sku_code, sku.name, sku.brand_name, sku.product_type, sku.category,
                sku.description, sku.net_content, sku.serving_size, sku.servings_per_container,
                sku.quantity, sku.unit_price, sku.storage_location,
                sku.manufacturer_name, sku.manufacturer_facility, sku.manufacturer_address,
                sku.manufacturer_city, sku.manufacturer_state, sku.manufacturer_country,
                sku.manufacturer_facility_id,
                sku.lot_number, sku.batch_number,
                sku.manufacturing_date.isoformat() if sku.manufacturing_date else "",
                sku.expiration_date.isoformat() if sku.expiration_date else "",
                sku.supplier_name, sku.supplier_contact, sku.supplier_email, sku.supplier_phone,
                sku.nsf_certification_type, sku.nsf_certification_status, sku.nsf_certification_number,
                sku.nsf_certification_date.isoformat() if sku.nsf_certification_date else "",
                sku.nsf_expiration_date.isoformat() if sku.nsf_expiration_date else "",
                sku.nsf_next_audit_date.isoformat() if sku.nsf_next_audit_date else "",
                sku.nsf_last_test_date.isoformat() if sku.nsf_last_test_date else "",
                "Yes" if sku.nsf_banned_substances_tested else "No",
                sku.nsf_test_results,
                sku.label_claims, sku.intended_use, sku.directions_for_use,
                sku.warnings, sku.allergens,
                sku.sds_document_url, sku.coa_document_url, sku.label_image_url,
                sku.primary_contact_name, sku.primary_contact_email, sku.primary_contact_phone,
                "Yes" if sku.is_active else "No",
                "Yes" if sku.requires_nsf_certification else "No",
                sku.notes
            ]

            if include_internal_notes:
                row.append(sku.internal_notes)

            writer.writerow(row)

        return output.getvalue()
