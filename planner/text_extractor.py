"""
Text Extractor Module

Extract typing text from
user commands.
"""


class TextExtractor:
    """
    Extract text content
    from typing commands.
    """

    def __init__(self):
        """
        Initialize Text Extractor.
        """

        self.type_commands = [
            "type",
            "write"
        ]
        
    def extract_text(self, command):
        """
        Extract text from
        typing command.
        """

        if not command:
            return None
        
        for keyword in self.type_commands:

            if command.lower().startswith(keyword):

                text = command[len(keyword):].strip()

                return text

        return None