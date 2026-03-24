def subtotal(lines):
    return sum(price * qty for price, qty in lines)
