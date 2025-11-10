# Trip Readiness Checker

print("Welcome to the Trip Readiness Checker!\n")

while True:
    gas = input("Is your gas tank at least half full? (yes/no): ").lower()
    oil = input("Have you checked your oil? (yes/no): ").lower()
    tires = input("Are your tires properly inflated? (yes/no): ").lower()
    lights = input("Are all your lights working? (yes/no): ").lower()

    # Check all responses
    if gas == "yes" and oil == "yes" and tires == "yes" and lights == "yes":
        print("You're ready to hit the road! 🚗")
    else:
        if gas == "no":
            print("Better stop for gas before you go.")
        if oil == "no":
            print("Check your oil level first.")
        if tires == "no":
            print("Inflate your tires before driving.")
        if lights == "no":
            print("Fix your lights to ensure safety.")
        if gas != "no" and oil != "no" and tires != "no" and lights != "no":
            print("Do a quick maintenance check before you leave.")

    # Ask if the user wants to check another trip
    again = input("\nCheck another trip? (yes/no): ").lower()
    if again != "yes":
        print("Drive safe!")
        break
