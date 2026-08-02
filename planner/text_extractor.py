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

            "write",

            "enter",

            "input",

            "insert",

            "type text",

            "write text"

        ]
        
    def extract_text(self, command):
        """
        Extract text from
        typing command.
        """

        if not command:
            return None
        
        command = command.strip()

        lower_command = command.lower()

        for keyword in self.type_commands:

            if lower_command.startswith(keyword):

                text = command[len(keyword):].strip()

                # Remove leading punctuation

                text = text.lstrip(" ,:-")

                # Remove surrounding quotes

                text = text.strip("\"'")

                return text


        # ---------------------------------
        # Compound Commands
        # ---------------------------------

        compound_keywords = [

            " and type ",

            " then type ",

            " and write ",

            " then write ",

            " and enter ",

            " then enter ",

            " and input ",

            " then input "

        ]

        for keyword in compound_keywords:

            if keyword in lower_command:

                text = command.split(keyword, 1)[1].strip()

                text = text.lstrip(" ,:-")

                text = text.strip("\"'")

                return text

        return None