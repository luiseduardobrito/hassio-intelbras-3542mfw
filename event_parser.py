import logging
import re
from typing import Optional, Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)


class IntelbrasEventParserError(Exception):
    """Custom exception for parser errors."""
    pass


class IntelbrasEventParser:
    """Safe parser for Intelbras 3542 MFW event data."""
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the parser.
        
        Args:
            strict_mode: If True, raise exceptions on parse errors. 
                        If False, log errors and continue parsing.
        """
        self.strict_mode = strict_mode
        self.record_pattern = re.compile(r'^records\[(\d+)\]\.([^=]+)=(.*)$')
        self.found_pattern = re.compile(r'^found=(\d+)$')

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Parse the raw data and return a list of events.
        
        Args:
            raw_data: Raw event data string
            
        Returns:
            List of parsed event dictionaries
            
        Raises:
            IntelbrasEventParserError: If strict_mode=True and parsing fails
        """
        if not isinstance(raw_data, str):
            error_msg = f"Expected string input, got {type(raw_data)}"
            if self.strict_mode:
                raise IntelbrasEventParserError(error_msg)
            logger.error(error_msg)
            return []

        if not raw_data.strip():
            logger.warning("Empty input data provided")
            return []

        events = []
        records = {}  # Store records by index
        
        for line_num, line in enumerate(raw_data.splitlines(), 1):
            line = line.strip()
            
            if not line:
                continue
                
            try:
                if line.startswith("records["):
                    self._parse_record_line(line, records, line_num)
                elif line.startswith("found="):
                    # Optional: store found count for validation
                    found_count = self._parse_found_line(line, line_num)
                    logger.debug(f"Found count: {found_count}")
                else:
                    logger.debug(f"Skipping unrecognized line {line_num}: {line}")
                    
            except Exception as e:
                error_msg = f"Error parsing line {line_num}: '{line}' - {e}"
                if self.strict_mode:
                    raise IntelbrasEventParserError(error_msg) from e
                logger.error(error_msg)
                continue

        # Convert records dict to sorted list
        if records:
            max_index = max(records.keys())
            for i in range(max_index + 1):
                if i in records:
                    events.append(records[i])
                else:
                    logger.warning(f"Missing record at index {i}")
                    if self.strict_mode:
                        raise IntelbrasEventParserError(f"Missing record at index {i}")

        logger.info(f"Successfully parsed {len(events)} events")
        return events
    
    def _parse_found_line(self, line: str, line_num: int) -> int:
        """
        Parse the found line and return the number of events.
        
        Args:
            line: The line to parse
            line_num: Line number for error reporting
            
        Returns:
            Number of events found
            
        Raises:
            IntelbrasEventParserError: If parsing fails
        """
        match = self.found_pattern.match(line)
        if not match:
            raise IntelbrasEventParserError(f"Invalid found line format: {line}")
        
        try:
            return int(match.group(1))
        except ValueError as e:
            raise IntelbrasEventParserError(f"Invalid found count: {match.group(1)}") from e
    
    def _parse_record_line(self, line: str, records: Dict[int, Dict[str, Any]], line_num: int) -> None:
        """
        Parse a record line and add it to the records dictionary.
        
        Args:
            line: The line to parse
            records: Dictionary to store parsed records
            line_num: Line number for error reporting
            
        Raises:
            IntelbrasEventParserError: If parsing fails
        """
        match = self.record_pattern.match(line)
        if not match:
            raise IntelbrasEventParserError(f"Invalid record line format: {line}")
        
        try:
            record_index = int(match.group(1))
            field_name = match.group(2)
            field_value = match.group(3)
        except (ValueError, IndexError) as e:
            raise IntelbrasEventParserError(f"Error extracting record components: {e}") from e
        
        # Validate field name
        if not field_name or not field_name.replace('_', '').replace('-', '').isalnum():
            logger.warning(f"Suspicious field name '{field_name}' on line {line_num}")
        
        # Initialize record if not exists
        if record_index not in records:
            records[record_index] = {}
        
        # Convert numeric values
        converted_value = self._convert_value(field_value, field_name, line_num)
        records[record_index][field_name] = converted_value
        
        logger.debug(f"Parsed: records[{record_index}].{field_name} = {converted_value}")
    
    def _convert_value(self, value: str, field_name: str, line_num: int) -> Any:
        """
        Convert string value to appropriate type based on field name and content.
        
        Args:
            value: String value to convert
            field_name: Name of the field (for context)
            line_num: Line number for error reporting
            
        Returns:
            Converted value (str, int, or original string if conversion fails)
        """
        if not value:
            return ""
        
        # Try to convert numeric fields
        numeric_fields = {
            'AttendanceState', 'CardType', 'CreateTime', 'Door', 'ErrorCode',
            'Mask', 'Method', 'ReaderID', 'RecNo', 'RemainingTimes', 
            'ReservedInt', 'Status', 'UserType'
        }
        
        if field_name in numeric_fields:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Expected numeric value for {field_name} on line {line_num}, got: {value}")
                if self.strict_mode:
                    raise IntelbrasEventParserError(f"Invalid numeric value for {field_name}: {value}")
        
        return value

