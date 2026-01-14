"""
Table Parser - Parse HTML tables into structured data

Extracts tabular data and makes it searchable.
Key for handling rate tables, etc.
"""

from typing import Dict, Any, List, Optional

from bs4 import Tag
from loguru import logger


class TableParser:
    """
    Parse HTML tables into structured data.
    
    This is important for structured lookups (rates, etc.)!
    """
    
    def parse_table(self, table: Tag) -> Optional[Dict[str, Any]]:
        """
        Parse an HTML table.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            Parsed table data with headers and rows
        """
        try:
            # Extract caption/title
            caption = self._extract_caption(table)
            
            # Extract headers
            headers = self._extract_headers(table)
            
            # Extract rows
            rows = self._extract_rows(table, len(headers))
            
            if not rows:
                return None
            
            # Create structured representation
            table_data = {
                "caption": caption,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(headers),
            }
            
            return table_data
            
        except Exception as e:
            logger.error(f"Error parsing table: {e}")
            return None
    
    def _extract_caption(self, table: Tag) -> str:
        """Extract table caption/title."""
        caption = table.find("caption")
        if caption:
            return caption.get_text(strip=True)
        
        # Try looking before the table for a heading
        prev = table.find_previous_sibling()
        if prev and prev.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return prev.get_text(strip=True)
        
        return "Untitled Table"
    
    def _extract_headers(self, table: Tag) -> List[str]:
        """
        Extract table headers.
        
        Looks in <thead> or first <tr>.
        """
        headers = []
        
        # Try <thead>
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
        
        # Fallback: first row
        if not headers:
            first_row = table.find("tr")
            if first_row:
                # Check if first row has <th> tags
                ths = first_row.find_all("th")
                if ths:
                    headers = [th.get_text(strip=True) for th in ths]
                else:
                    # Use first row as headers
                    headers = [td.get_text(strip=True) for td in first_row.find_all("td")]
        
        # Fallback: generate column names
        if not headers:
            # Count columns in first data row
            tbody = table.find("tbody") or table
            first_data_row = tbody.find("tr")
            if first_data_row:
                num_cols = len(first_data_row.find_all(["td", "th"]))
                headers = [f"Column {i+1}" for i in range(num_cols)]
        
        return headers
    
    def _extract_rows(self, table: Tag, num_columns: int) -> List[List[str]]:
        """
        Extract table rows.
        
        Args:
            table: Table element
            num_columns: Expected number of columns
            
        Returns:
            List of rows (each row is list of cell values)
        """
        rows = []
        
        # Find tbody or use table directly
        tbody = table.find("tbody") or table
        
        # Skip first row if it was used for headers
        all_rows = tbody.find_all("tr")
        
        # Determine if first row is headers
        skip_first = False
        if all_rows:
            first_row = all_rows[0]
            if first_row.find("th"):
                skip_first = True
        
        # Extract data rows
        for tr in all_rows[1:] if skip_first else all_rows:
            cells = tr.find_all(["td", "th"])
            
            if len(cells) != num_columns:
                # Skip rows that don't match column count
                continue
            
            row = [cell.get_text(strip=True) for cell in cells]
            rows.append(row)
        
        return rows
    
    def table_to_records(self, table_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert table to list of record dicts.
        
        Args:
            table_data: Parsed table data
            
        Returns:
            List of records (each row as a dict)
        """
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        
        records = []
        for row in rows:
            record = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    record[headers[i]] = value
            records.append(record)
        
        return records
    
    def detect_rate_table(self, table_data: Dict[str, Any]) -> bool:
        """
        Detect if table is a rate table.
        
        Looks for common rate table patterns.
        
        Args:
            table_data: Parsed table data
            
        Returns:
            True if likely a rate table
        """
        # Check caption
        caption = table_data.get("caption", "").lower()
        if any(term in caption for term in ["rate", "price", "cost", "fee"]):
            return True
        
        # Check headers
        headers = [h.lower() for h in table_data.get("headers", [])]
        if any(term in " ".join(headers) for term in ["rate", "price", "amount", "cost"]):
            return True
        
        return False
    
    def extract_location_rates(self, table_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract location-based rates from table.
        
        This is specifically useful for per diem tables!
        
        Args:
            table_data: Parsed table data
            
        Returns:
            List of location rate records
        """
        records = self.table_to_records(table_data)
        
        # Try to identify location and rate columns
        headers = [h.lower() for h in table_data.get("headers", [])]
        
        location_col = None
        rate_col = None
        
        # Find location column
        for i, header in enumerate(headers):
            if any(term in header for term in ["location", "city", "place", "destination"]):
                location_col = i
                break
        
        # Find rate column
        for i, header in enumerate(headers):
            if any(term in header for term in ["rate", "amount", "price", "per diem", "daily"]):
                rate_col = i
                break
        
        if location_col is None or rate_col is None:
            logger.debug("Could not identify location/rate columns")
            return []
        
        # Extract rate records
        location_rates = []
        for record in records:
            header_list = table_data.get("headers", [])
            if location_col < len(header_list) and rate_col < len(header_list):
                location = record.get(header_list[location_col])
                rate = record.get(header_list[rate_col])
                
                if location and rate:
                    location_rates.append({
                        "location": location,
                        "rate": rate,
                        "type": "location_rate",
                        "source_table": table_data.get("caption", "Rate Table"),
                    })
        
        return location_rates
