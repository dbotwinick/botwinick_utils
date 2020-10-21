# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

import operator
from functools import reduce
from struct import calcsize, error, pack, unpack

from six import string_types

_BINARY_FLOAT_PACK = '!f'
_BINARY_INTEGER_PACK = '!I'
_BINARY_STRING_PACK = '!s'


def bytes_size(shape, struct=_BINARY_FLOAT_PACK, return_length=True):
    if isinstance(shape, (int, float)):
        shape = [shape]
    elif not isinstance(shape, (tuple, list)):
        shape = [shape]

    if not isinstance(struct, string_types):
        if struct == float:
            struct = _BINARY_FLOAT_PACK
        elif struct == int:
            struct = _BINARY_INTEGER_PACK
        elif struct == str:
            struct = _BINARY_STRING_PACK
        else:
            raise ValueError('unsupported struct item type')

    length = reduce(operator.mul, shape)
    size = calcsize(struct) * length
    if not return_length:
        return size
    return size, length


def unpack_sequence(f, shape, data_type=float, wrapper_type=list):
    if data_type == float:
        struct = _BINARY_FLOAT_PACK
    elif data_type == int:
        struct = _BINARY_INTEGER_PACK
    elif data_type in string_types:
        struct = _BINARY_STRING_PACK
    else:
        raise ValueError('unsupported struct item type')
    size, length = bytes_size(shape, struct, return_length=True)
    data = f.read(size)  # type: bytes
    if len(data) != size:
        raise ValueError('bytes length mismatch between expected shape and file handle; expected=%d, actual=%d' % (size, len(data)))
    fmt = ''.join([struct[0]] + [struct[1]] * length)
    return wrapper_type(unpack(fmt, data))


def pack_sequence(f, sequence):
    if isinstance(sequence[0], float):
        struct = _BINARY_FLOAT_PACK
    elif isinstance(sequence[0], int):
        struct = _BINARY_INTEGER_PACK
    elif isinstance(sequence[0], string_types):
        struct = _BINARY_STRING_PACK
    else:
        raise ValueError('unsupported struct item type')
    size, length = bytes_size(len(sequence), struct, return_length=True)
    fmt = ''.join([struct[0]] + [struct[1]] * length)
    f.write(pack(fmt, *sequence))


__all__ = 'pack_sequence', 'unpack_sequence', 'error', 'bytes_size', 'calcsize', 'unpack', 'pack'
