"""Pure-Python Ed25519 (RFC 8032 section 5.1), standard library only.

It stands in for the enclave's crypto library so the kit runs with no installs. It is slow (milliseconds per
operation) and not constant-time, which is fine for verifying a public signature and for signing test fixtures, and
wrong for a production signer: there the private key lives in the HSM and signing uses OpenSSF `model_signing`
(PKCS#11) or cosign, and verification uses a vetted library such as `cryptography`.
"""
import hashlib

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


class InvalidSignature(Exception):
    """Raised by verify() for any malformed or non-matching signature."""


def _h(data: bytes) -> int:
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


def _add(a, b):  # extended twisted-Edwards coordinates (X, Y, Z, T)
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    pa, pb = (y1 - x1) * (y2 - x2) % P, (y1 + x1) * (y2 + x2) % P
    pc, pd = t1 * 2 * D * t2 % P, z1 * 2 * z2 % P
    e, f, g, h = pb - pa, pd - pc, pd + pc, pb + pa
    return e * f % P, g * h % P, f * g % P, e * h % P


def _mul(s: int, pt):
    q = (0, 1, 1, 0)
    while s:
        if s & 1:
            q = _add(q, pt)
        pt, s = _add(pt, pt), s >> 1
    return q


def _recover_x(y: int, sign: int):
    if y >= P:
        return None
    x2 = (y * y - 1) * pow(D * y * y + 1, P - 2, P)
    if x2 % P == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    return P - x if (x & 1) != sign else x


_GY = 4 * pow(5, P - 2, P) % P
_GX = _recover_x(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)


def _compress(pt) -> bytes:
    zinv = pow(pt[2], P - 2, P)
    x, y = pt[0] * zinv % P, pt[1] * zinv % P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _decompress(raw: bytes):
    y = int.from_bytes(raw, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def _expand(secret: bytes):
    if len(secret) != 32:
        raise ValueError("an Ed25519 private key is 32 bytes")
    digest = hashlib.sha512(secret).digest()
    a = int.from_bytes(digest[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return a, digest[32:]


def public_key(secret: bytes) -> bytes:
    return _compress(_mul(_expand(secret)[0], G))


def sign(secret: bytes, msg: bytes) -> bytes:
    a, prefix = _expand(secret)
    pub = _compress(_mul(a, G))
    r = _h(prefix + msg) % L
    big_r = _compress(_mul(r, G))
    s = (r + _h(big_r + pub + msg) % L * a) % L
    return big_r + s.to_bytes(32, "little")


def verify(pub: bytes, msg: bytes, sig: bytes) -> None:
    """Return None if `sig` is a valid signature of `msg` under `pub`; raise InvalidSignature otherwise."""
    if len(pub) != 32 or len(sig) != 64:
        raise InvalidSignature("bad key or signature length")
    a, r = _decompress(pub), _decompress(sig[:32])
    s = int.from_bytes(sig[32:], "little")
    if a is None or r is None or s >= L:
        raise InvalidSignature("malformed key or signature")
    lhs, rhs = _mul(s, G), _add(r, _mul(_h(sig[:32] + pub + msg) % L, a))
    if (lhs[0] * rhs[2] - rhs[0] * lhs[2]) % P or (lhs[1] * rhs[2] - rhs[1] * lhs[2]) % P:
        raise InvalidSignature("signature does not match")
