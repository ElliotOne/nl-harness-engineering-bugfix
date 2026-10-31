def shipping_pence(subtotal_pence: int) -> int:
    if subtotal_pence < 0:
        raise ValueError("subtotal must be nonnegative")
    return 0 if subtotal_pence >= 5000 else 499
