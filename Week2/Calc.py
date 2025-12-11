print("Simple Python Calculator")
print("Type 'q' at any time to quit.\n")

while True:
    # first number
    num1_input = input("Enter the first number: ")
    if num1_input.lower() == 'q':
        print("Goodbye!")
        break

    try:
        num1 = float(num1_input)
    except ValueError:
        print("Error: Please enter a valid number.\n")
        continue

    # operator
    op = input("Enter operator (+, -, *, /): ").strip()
    if op.lower() == 'q':
        print("Goodbye!")
        break
    elif op not in ['+', '-', '*', '/']:
        print("Error: Invalid operator. Please use +, -, *, or /.\n")
        continue

    # second number
    num2_input = input("Enter the second number: ")
    if num2_input.lower() == 'q':
        print("Goodbye!")
        break

    try:
        num2 = float(num2_input)
    except ValueError:
        print("Error: Please enter a valid number.\n")
        continue

    # calculation and validation
    if op == '+':
        result = num1 + num2
    elif op == '-':
        result = num1 - num2
    elif op == '*':
        result = num1 * num2
    elif op == '/':
        if num2 == 0:
            print("Error: Cannot divide by zero.\n")
            continue
        else:
            result = num1 / num2

    # result
    print(f"Result: {result}\n")
