from logging import Logger
from typing import Any, Callable, Generator

from core.transformers import AbstractTextWordTokenizerTransformer, AbstractTransformer
from core.transformers import ItemUpdaterCallbackTransformer

class ArabicTextWordsTokenizerTransformer(AbstractTextWordTokenizerTransformer):
    def __init__(self, logger: Logger, 
                input_key_path: list[str],
                output_key: str) -> None:
        super().__init__(logger, input_key_path, output_key)

    def _tokenize_text(self, text: str, item: dict, context: dict) -> Generator[list[dict], None, None]:
        import re
                    
        arabic_words = re.findall(r'[َُِْـًٌٍّؤائءآىإأبتثجحخدذرزسشصضطظعغفقكلمنهـوي]+', text)
        for txt in arabic_words:
            words = txt.replace('×', '').replace(' ', '\n').replace('\r', '\n').replace('\t', '\n').split('\n')
            for w in words:
                if w and w.strip():
                    yield w

class ArabicRemoveDiacFromWordTransformer(ItemUpdaterCallbackTransformer):
    def __init__(self, logger: Logger, 
                input_key_path: list[str], 
                input_value_type: Any, 
                output_key: str) -> None:
        super().__init__(logger, input_key_path, input_value_type, output_key, callback=ArabicRemoveDiacFromWordTransformer.remove_diac)

    def remove_diac(text: str) -> str:
        if text is None:
            return text
        return text.replace('َ', '').replace('ّ', '').replace('ِ', '').replace('ُ', '').replace('ْ', '').replace('ً', '').replace('ٌ', '').replace('ٍ', '')