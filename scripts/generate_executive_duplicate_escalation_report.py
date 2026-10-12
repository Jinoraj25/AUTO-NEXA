import os
import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\data\overall_catalogue.db"
OUTPUT_EXCEL = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\Executive_Catalog_Audit_and_Duplicate_Escalation_Report_v3.xlsx"



conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("1. Generating Sheet 1: Brand-Wise Master Breakdown...")
query_sheet1 = """
    SELECT 
        brand_name,
        COALESCE(NULLIF(aggregate, ''), 'Mechanical Parts') AS category,
        COUNT(DISTINCT line_code_part_number) AS unique_sku_count,
        COUNT(*) AS total_db_records
    FROM overall_catalogue
    WHERE brand_name IS NOT NULL AND brand_name != ''
    GROUP BY brand_name
    ORDER BY total_db_records DESC
"""
df_sheet1 = pd.read_sql_query(query_sheet1, conn)

total_db_records = df_sheet1['total_db_records'].sum()
df_sheet1['contribution_pct'] = (df_sheet1['total_db_records'] / total_db_records) * 100

# Reorder columns
df_sheet1 = df_sheet1[['brand_name', 'category', 'unique_sku_count', 'total_db_records', 'contribution_pct']]
df_sheet1.columns = ['Brand Name', 'Category / System Aggregate', 'Unique SKU Part Count', 'Total DB Records', 'Contribution %']

print(f"Sheet 1 data ready: {len(df_sheet1)} brands, total records: {total_db_records:,}")

print("2. Generating Sheet 2: Duplicate Escalation Breakdown...")

# Top 50 most duplicated records across the database
query_sheet2_top = """
    SELECT 
        brand_name,
        line_code,
        line_code_part_number,
        part_description,
        vehicle_make,
        vehicle_model,
        COUNT(*) AS duplicate_repeat_count
    FROM overall_catalogue
    GROUP BY 
        line_code, brand_name, line_code_part_number, part_description,
        hsn_code, tax_rate, price_type, sales_uom, list_price, mrp_price,
        sales_price_group, vehicle_segment, vehicle_make, vehicle_model,
        vehicle_sub_model, vehicle_fuel_type, vehicle_from_year, vehicle_to_year,
        aggregate, sub_aggregate, components
    HAVING duplicate_repeat_count > 1
    ORDER BY duplicate_repeat_count DESC
    LIMIT 100
"""
df_top_duplicates = pd.read_sql_query(query_sheet2_top, conn)

# Overall summary by brand of duplicate rows (Fast GROUP BY)
query_sheet2_brand_dups = """
    SELECT 
        brand_name,
        SUM(cnt) AS total_rows,
        COUNT(*) AS unique_rows,
        (SUM(cnt) - COUNT(*)) AS duplicate_rows_count
    FROM (
        SELECT 
            brand_name,
            COUNT(*) AS cnt
        FROM overall_catalogue
        WHERE brand_name IS NOT NULL AND brand_name != ''
        GROUP BY 
            line_code, brand_name, line_code_part_number, part_description,
            hsn_code, tax_rate, price_type, sales_uom, list_price, mrp_price,
            sales_price_group, vehicle_segment, vehicle_make, vehicle_model,
            vehicle_sub_model, vehicle_fuel_type, vehicle_from_year, vehicle_to_year,
            aggregate, sub_aggregate, components
    )
    GROUP BY brand_name
    HAVING duplicate_rows_count > 0
    ORDER BY duplicate_rows_count DESC
"""
df_brand_dups = pd.read_sql_query(query_sheet2_brand_dups, conn)
df_brand_dups['duplicate_pct'] = (df_brand_dups['duplicate_rows_count'] / df_brand_dups['total_rows']) * 100
df_brand_dups.columns = ['Brand Name', 'Total DB Rows', 'Unique Data Rows', 'Duplicate Rows Count', 'Duplicate %']


conn.close()

# Write Excel workbook using openpyxl for formatting
with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    df_sheet1.to_excel(writer, sheet_name='Brand Master Breakdown', index=False)
    
    # Create Sheet 2 with executive summary + top duplicate examples + brand summary
    wb = writer.book
    ws2 = wb.create_sheet(title='Duplicate Escalation Report')
    
    # Executive Summary Title block in Sheet 2
    ws2.append(["EXECUTIVE DUPLICATE ESCALATION AUDIT REPORT"])
    ws2.append(["Subject: Root Cause Analysis of 7,044,191 Duplicate Lines in Catalog Data Source Files"])
    ws2.append([])
    ws2.append(["KEY FINDINGS & ESCALATION SUMMARY:"])
    ws2.append(["• Total Ingested Catalog Rows across 59 Files:", "23,651,457 rows"])
    ws2.append(["• Total 100% Unique Data Rows:", "16,607,266 rows"])
    ws2.append(["• Total 100% Identical Duplicate Rows:", "7,044,191 rows (29.78% Data Inflation)"])
    ws2.append(["• Total Distinct SKU Part Numbers:", "415,542 SKUs"])
    ws2.append(["• Root Cause:", "Source catalog Excel files (e.g. Sheet_47.xlsx, Sheet_3.xlsx) contain thousands of physically copy-pasted identical rows in the raw sheets."])
    ws2.append([])
    
    # Section 1 Header: Top Egregious Duplicate Part Examples
    ws2.append(["SECTION 1: TOP EGREGIOUS DUPLICATE EXAMPLES (REPEATED HUNDREDS OF TIMES IN SOURCE FILES)"])
    ws2.append(['Brand Name', 'Line Code', 'Part Number SKU', 'Part Description', 'Vehicle Make', 'Vehicle Model', 'Duplicate Repeats Count in File'])
    
    for idx, r in df_top_duplicates.iterrows():
        ws2.append([
            r['brand_name'], r['line_code'], r['line_code_part_number'],
            r['part_description'], r['vehicle_make'], r['vehicle_model'], r['duplicate_repeat_count']
        ])
        
    ws2.append([])
    ws2.append(["SECTION 2: BRAND-WISE DUPLICATE IMPACT SUMMARY"])
    ws2.append(['Brand Name', 'Total DB Rows', 'Unique Data Rows', 'Duplicate Rows Count', 'Duplicate %'])
    
    for idx, r in df_brand_dups.iterrows():
        ws2.append([
            r['Brand Name'], r['Total DB Rows'], r['Unique Data Rows'],
            r['Duplicate Rows Count'], round(r['Duplicate %'], 2)
        ])

print("Applying professional formatting to Excel workbook...")

# Load workbook to apply styles
wb = openpyxl.load_workbook(OUTPUT_EXCEL)

# Style colors
navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
dark_red_fill = PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid")
light_red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
gray_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

white_bold_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F497D")
section_font = Font(name="Calibri", size=12, bold=True, color="9C0006")
bold_font = Font(name="Calibri", size=11, bold=True)
regular_font = Font(name="Calibri", size=11)

thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

# Format Sheet 1
ws1 = wb['Brand Master Breakdown']
for col in range(1, ws1.max_column + 1):
    cell = ws1.cell(row=1, column=col)
    cell.fill = navy_fill
    cell.font = white_bold_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

for row in range(2, ws1.max_row + 1):
    ws1.cell(row=row, column=3).number_format = '#,##0'
    ws1.cell(row=row, column=4).number_format = '#,##0'
    ws1.cell(row=row, column=5).number_format = '0.00"%"'
    for col in range(1, ws1.max_column + 1):
        ws1.cell(row=row, column=col).border = thin_border

for col in ws1.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws1.column_dimensions[col_letter].width = max(max_len + 4, 15)

# Format Sheet 2
ws2 = wb['Duplicate Escalation Report']
ws2.cell(row=1, column=1).font = title_font
ws2.cell(row=2, column=1).font = section_font

for row in range(4, 10):
    ws2.cell(row=row, column=1).font = bold_font

for row in ws2.iter_rows(min_row=1, max_row=ws2.max_row):
    for cell in row:
        val = str(cell.value or '')
        if "SECTION 1" in val or "SECTION 2" in val:
            cell.font = section_font
        elif val in ['Brand Name', 'Line Code', 'Part Number SKU', 'Part Description', 'Vehicle Make', 'Vehicle Model', 'Duplicate Repeats Count in File', 'Total DB Rows', 'Unique Data Rows', 'Duplicate Rows Count', 'Duplicate %']:
            cell.fill = dark_red_fill
            cell.font = white_bold_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

for col in ws2.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws2.column_dimensions[col_letter].width = min(max(max_len + 4, 15), 50)

wb.save(OUTPUT_EXCEL)
print(f"Report successfully saved to: {OUTPUT_EXCEL}")
print(f"File size: {round(os.path.getsize(OUTPUT_EXCEL)/(1024*1024), 2)} MB")
