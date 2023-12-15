import re


def validate_username(username):
    pattern = r'^[A-Za-z0-9._]{4,30}$'
    if re.match(pattern, username):
        return True
    return False


def validate_password(password):
    pattern = r'^(?=.*[A-Z])(?=.*\d).{8,16}$'
    if re.match(pattern, password):
        return True
    return False
