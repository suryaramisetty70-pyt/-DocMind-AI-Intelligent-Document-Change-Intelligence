"""Excel and CSV comparison engine."""
from typing import Dict, Any, List
try:
    import pandas as pd
except ImportError:
    pd = None
import io
from openpyxl import load_workbook


class ExcelComparisonEngine:
    """Engine for comparing Excel and CSV files."""

    @staticmethod
    def extract_excel_data(excel_content: bytes) -> Dict[str, Any]:
        """Extract all sheets and data from Excel file."""
        data = {"sheets": {}}
        
        if pd is None:
            return {"error": "Pandas is not installed. Excel comparison is temporarily disabled."}
        
        try:
            # Read with pandas for easy data access
            excel_file = pd.ExcelFile(io.BytesIO(excel_content))
            data["sheet_names"] = excel_file.sheet_names
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                data["sheets"][sheet_name] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "data": df.to_dict(orient="records")
                }
        except Exception as e:
            data["error"] = str(e)
        
        return data

    @staticmethod
    def extract_csv_data(csv_content: bytes) -> Dict[str, Any]:
        """Extract data from CSV file."""
        data = {}
        
        if pd is None:
            return {"error": "Pandas is not installed. CSV comparison is temporarily disabled."}
        
        try:
            df = pd.read_csv(io.BytesIO(csv_content))
            data = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "data": df.to_dict(orient="records")
            }
        except Exception as e:
            data["error"] = str(e)
        
        return data

    @staticmethod
    def compare_excels(excel1_content: bytes, excel2_content: bytes) -> Dict[str, Any]:
        """Compare two Excel files."""
        data1 = ExcelComparisonEngine.extract_excel_data(excel1_content)
        data2 = ExcelComparisonEngine.extract_excel_data(excel2_content)
        
        if "error" in data1 or "error" in data2:
            return {"error": "Failed to read Excel files"}
        
        sheet_names1 = data1.get("sheet_names", [])
        sheet_names2 = data2.get("sheet_names", [])
        
        # Find common sheets
        common_sheets = set(sheet_names1) & set(sheet_names2)
        only_in_file1 = set(sheet_names1) - set(sheet_names2)
        only_in_file2 = set(sheet_names2) - set(sheet_names1)
        
        sheet_comparisons = {}
        total_similarity = 0
        total_sheets = 0
        
        for sheet in common_sheets:
            sheet1_data = data1["sheets"][sheet]
            sheet2_data = data2["sheets"][sheet]
            
            # Compare structure
            struct_match = (
                sheet1_data["columns"] == sheet2_data["columns"] and
                sheet1_data["column_names"] == sheet2_data["column_names"]
            )
            
            # Compare data
            df1 = pd.DataFrame(sheet1_data["data"])
            df2 = pd.DataFrame(sheet2_data["data"])
            
            # Align dataframes for comparison
            try:
                merged = df1.compare(df2)
                differences = len(merged)
            except:
                differences = "Unable to calculate"
            
            # Calculate similarity
            if len(df1) == len(df2):
                matching_rows = sum(1 for d1, d2 in zip(df1.to_dict(orient="records"), df2.to_dict(orient="records")) if d1 == d2)
                similarity = matching_rows / len(df1) if len(df1) > 0 else 1.0
            else:
                similarity = 0.5
            
            total_similarity += similarity
            total_sheets += 1
            
            sheet_comparisons[sheet] = {
                "structure_match": struct_match,
                "rows_file1": sheet1_data["rows"],
                "rows_file2": sheet2_data["rows"],
                "columns_match": sheet1_data["columns"] == sheet2_data["columns"],
                "column_names_match": sheet1_data["column_names"] == sheet2_data["column_names"],
                "differences": differences,
                "similarity_score": similarity
            }
        
        return {
            "type": "excel",
            "sheet_names_file1": sheet_names1,
            "sheet_names_file2": sheet_names2,
            "common_sheets": list(common_sheets),
            "only_in_file1": list(only_in_file1),
            "only_in_file2": list(only_in_file2),
            "sheet_comparisons": sheet_comparisons,
            "overall_similarity": total_similarity / total_sheets if total_sheets > 0 else 0,
            "total_sheets_compared": total_sheets
        }

    @staticmethod
    def compare_csvs(csv1_content: bytes, csv2_content: bytes) -> Dict[str, Any]:
        """Compare two CSV files."""
        data1 = ExcelComparisonEngine.extract_csv_data(csv1_content)
        data2 = ExcelComparisonEngine.extract_csv_data(csv2_content)
        
        if "error" in data1 or "error" in data2:
            return {"error": "Failed to read CSV files"}
        
        # Compare columns
        columns_match = data1["column_names"] == data2["column_names"]
        
        # Compare data
        df1 = pd.DataFrame(data1["data"])
        df2 = pd.DataFrame(data2["data"])
        
        try:
            merged = df1.compare(df2)
            differences = len(merged)
        except:
            differences = "Unable to calculate"
        
        # Calculate similarity
        if len(df1) == len(df2):
            matching_rows = sum(1 for d1, d2 in zip(df1.to_dict(orient="records"), df2.to_dict(orient="records")) if d1 == d2)
            similarity = matching_rows / len(df1) if len(df1) > 0 else 1.0
        else:
            similarity = 0.5
        
        return {
            "type": "csv",
            "columns_match": columns_match,
            "column_names_file1": data1["column_names"],
            "column_names_file2": data2["column_names"],
            "rows_file1": data1["rows"],
            "rows_file2": data2["rows"],
            "differences": differences,
            "similarity_score": similarity
        }