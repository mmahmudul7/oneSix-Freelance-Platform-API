from django.core.exceptions import ValidationError


def validate_file_size(file):
    """ This validator validate if file size is less than 2 MB """
    max_size = 2
    max_size_in_bytes = max_size * 1024 * 1024

    if file.size > max_size_in_bytes:
        raise ValidationError(f"File '{file.name}' cannot be larger than {max_size}MB!")

def delivery_validate_file_size(file):
    """ This validator validate if file size is less than 1 GB """
    max_size = 1024
    max_size_in_bytes = max_size * 1024 * 1024

    if file.size > max_size_in_bytes:
        raise ValidationError(f"File '{file.name}' cannot be larger than {max_size}GB!")