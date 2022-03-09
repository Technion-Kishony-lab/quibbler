from enum import Enum


class SaveFormat(str, Enum):

    TXT = 'txt'
    BIN = 'binary'
    VALUE_TXT = 'value_txt'


SAVEFORMAT_TO_FILE_EXT = {
    SaveFormat.BIN: '.quib',
    SaveFormat.TXT: '.txt',
    SaveFormat.VALUE_TXT: '.txt',
}
