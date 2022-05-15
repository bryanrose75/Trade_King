def validate_float_format(text: str) -> bool:

    if text == "":
        return True

    if all(positive_float in "0123456789." for positive_float in text) and text.count(".") <= 1:
        try:
            float(text)
            return True
        except ValueError:
            return False

    else:
        return False


def validate_integer_format(text: str) -> bool:

    if text == "":
        return True

    if all(positive_int in "0123456789" for positive_int in text):
        try:
            int(text)
            return True
        except ValueError:
            return False

    else:
        return False



