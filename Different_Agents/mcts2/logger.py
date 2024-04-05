from datetime import datetime
from os import listdir

from mcts2.typedefs import BoardModError, SuccessMessage

class Logger:
    def __init__(self) -> None:
        prev_num_files = len(listdir("Logs/"))
        self.curr_file_name = f"Logs/Log{prev_num_files:03d}.log"

    def log_board_result(self, result: SuccessMessage | BoardModError):
        message: str
        if type(result) == SuccessMessage:
            message = str(result)
        else:
            assert type(result) == BoardModError
            message = str(result.value)

        message = f"{message} @ DATETIME {datetime.now()}\n"

        with open(self.curr_file_name, 'a', encoding='utf-8') as file:
            file.write(message)

