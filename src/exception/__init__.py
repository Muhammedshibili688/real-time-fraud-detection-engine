import sys
from src.logger import logging

def error_message_detail(error, error_detail: sys):
    """
    Extracts the file name and line number where the error occurred.
    """
    # exc_tb contains the 'traceback' (the history of the error)
    _, _, exc_tb = error_detail.exc_info()
    
    # Get the filename where the error happened
    file_name = exc_tb.tb_frame.f_code.co_filename
    
    # Get the line number
    line_number = exc_tb.tb_lineno

    # Create a formatted message
    error_message = "Error occurred in python script name [{0}] line number [{1}] error message [{2}]".format(
        file_name, line_number, str(error)
    )

    return error_message

class FraudException(Exception):
    def __init__(self, error_message, error_detail: sys):
        """
        :param error_message: error message in string format
        :param error_detail: sys module containing traceback info
        """
        super().__init__(error_message)
        
        # Capture the surgical details (File + Line)
        self.error_message = error_message_detail(
            error_message, error_detail=error_detail
        )
        
        # AUTOMATIC LOGGING: Log the surgical error as soon as it happens
        logging.error(self.error_message)

    def __str__(self):
        """
        Ensures that when we print(e), we see the detailed surgical message.
        """
        return self.error_message