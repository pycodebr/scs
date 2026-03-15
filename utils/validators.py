import re

from django.core.exceptions import ValidationError


def _only_digits(value):
    return re.sub(r'\D', '', value)


def validate_cpf(value):
    digits = _only_digits(value)
    if len(digits) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')
    if digits == digits[0] * 11:
        raise ValidationError('CPF inválido.')
    for i in range(9, 11):
        total = sum(int(digits[j]) * ((i + 1) - j) for j in range(i))
        remainder = total % 11
        digit = 0 if remainder < 2 else 11 - remainder
        if int(digits[i]) != digit:
            raise ValidationError('CPF inválido.')


def validate_cnpj(value):
    digits = _only_digits(value)
    if len(digits) != 14:
        raise ValidationError('CNPJ deve conter 14 dígitos.')
    if digits == digits[0] * 14:
        raise ValidationError('CNPJ inválido.')
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(digits[i]) * weights_1[i] for i in range(12))
    remainder = total % 11
    digit_1 = 0 if remainder < 2 else 11 - remainder
    if int(digits[12]) != digit_1:
        raise ValidationError('CNPJ inválido.')
    total = sum(int(digits[i]) * weights_2[i] for i in range(13))
    remainder = total % 11
    digit_2 = 0 if remainder < 2 else 11 - remainder
    if int(digits[13]) != digit_2:
        raise ValidationError('CNPJ inválido.')


def validate_cpf_cnpj(value):
    digits = _only_digits(value)
    if len(digits) == 11:
        validate_cpf(value)
    elif len(digits) == 14:
        validate_cnpj(value)
    else:
        raise ValidationError('CPF deve conter 11 dígitos ou CNPJ deve conter 14 dígitos.')
