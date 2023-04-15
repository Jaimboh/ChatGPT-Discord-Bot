import os
import logging
import logging.handlers
import boto3

class CustomFormatter(logging.Formatter):
    __LEVEL_COLORS = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]
    __FORMATS = None

    @classmethod
    def get_formats(cls):
        if cls.__FORMATS is None:
            cls.__FORMATS = {
                level: logging.Formatter(
                    f'\x1b[30;1m%(asctime)s\x1b[0m {color}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m -> %(message)s',
                    '%Y-%m-%d %H:%M:%S'
                )
                for level, color in cls.__LEVEL_COLORS
            }
        return cls.__FORMATS

    def format(self, record):
        formatter = self.get_formats().get(record.levelno)
        if formatter is None:
            formatter = self.get_formats()[logging.DEBUG]
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)
        record.exc_text = None
        return output


class LoggerFactory:
    @staticmethod
    def create_logger(formatter, handlers):
        logger = logging.getLogger('chatgpt_logger')
        logger.setLevel(logging.INFO)
        for handler in handlers:
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


class S3FileHandler(logging.FileHandler):
    def __init__(self, bucket_name, key):
        self.bucket_name = bucket_name
        self.key = key
        super().__init__(self.get_file_path())

    def get_file_path(self):
        if not os.path.exists('/tmp/logs'):
            os.makedirs('/tmp/logs')
        return '/tmp/logs/' + self.key

    def emit(self, record):
        super().emit(record)
        s3 = boto3.client('s3')
        with open(self.get_file_path(), 'rb') as f:
            s3.upload_fileobj(f, self.bucket_name, self.key)


# create S3FileHandler instead of FileHandler
file_handler = S3FileHandler('dicordbot', 'Discord-bot-log-folder')
console_handler = logging.StreamHandler()

formatter = CustomFormatter()
logger = LoggerFactory.create_logger(formatter, [file_handler, console_handler])
