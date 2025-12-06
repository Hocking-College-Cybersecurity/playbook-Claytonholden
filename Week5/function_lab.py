import math

# ---------- Reusable functions ----------

def add(a: float, b: float) -> float:
    """
    Return the sum of two numbers.
    Inputs: a (float), b (float)
    Output: float
    """
    return a + b


def hypotenuse(leg_a: float, leg_b: float) -> float:
    """
    Return the hypotenuse length using the Pythagorean theorem.
    Inputs: leg_a (float), leg_b (float)
    Output: float
    """
    return math.hypot(leg_a, leg_b)


def tip_amount(subtotal: float, tip_percent: float) -> float:
    """
    Return the tip value given a subtotal and tip percent.
    Inputs: subtotal (float), tip_percent (float, e.g., 20 for 20%)
    Output: float tip value
    """
    return subtotal * (tip_percent / 100.0)


def sale_price(price: float, percent_off: float) -> float:
    """
    Return the price after a percentage discount.
    Inputs: price (float), percent_off (float, e.g., 20 for 20% off)
    Output: float final price
    """
    discount = price * (percent_off / 100.0)
    return price - discount


# ---------- Input helpers (validation) ----------

def get_float(prompt: str) -> float:
    """Prompt until the user enters a valid float number."""
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number.")


def get_menu_choice() -> str:
    """Prompt until user selects a valid menu option."""
    while True:
        choice = input("Choose an option (1-5): ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("Please enter 1, 2, 3, 4, or 5.")


# ---------- Main program ----------

def main() -> None:
    print("=== Function Lab Demo ===")
    print("This program demonstrates reusable functions with input validation.\n")

    while True:
        print("\nMenu:")
        print("  1) Add two numbers")
        print("  2) Pythagorean theorem (right triangle hypotenuse)")
        print("  3) Tip calculator")
        print("  4) Sale price calculator")
        print("  5) Quit")

        choice = get_menu_choice()

        if choice == "1":
            print("\n[ADD] add(a, b)")
            a = get_float("Enter a: ")
            b = get_float("Enter b: ")
            result = add(a, b)
            print(f"Result: {a} + {b} = {result}")

        elif choice == "2":
            print("\n[PYTHAGOREAN THEOREM] hypotenuse(leg_a, leg_b)")
            a = get_float("Enter leg a: ")
            b = get_float("Enter leg b: ")
            c = hypotenuse(a, b)
            print(f"Hypotenuse = {c:.4f}")

        elif choice == "3":
            print("\n[TIP CALCULATOR] tip_amount(subtotal, tip_percent)")
            subtotal = get_float("Enter meal subtotal: $")
            tip_pct = get_float("Enter tip percent (e.g., 20 for 20%): ")
            tip = tip_amount(subtotal, tip_pct)
            total = subtotal + tip
            print(f"Tip: ${tip:.2f}  |  Total: ${total:.2f}")

        elif choice == "4":
            print("\n[SALE PRICE] sale_price(price, percent_off)")
            price = get_float("Enter original price: $")
            off = get_float("Enter percent off (e.g., 20 for 20%): ")
            final = sale_price(price, off)
            print(f"Final price after {off:.2f}% off: ${final:.2f}")

        elif choice == "5":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
