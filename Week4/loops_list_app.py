print("Loops & Lists App")

# start with an empty list
items = []
# menu loop
while True:  
    print("\nMenu:")
    print("1) Add an item")
    print("2) Remove an item")
    print("3) Show all items")
    print("4) Count items")
    print("5) Exit")

    choice = input("Choose 1-5: ")

    if choice == "1":
        new = input("Enter something to add: ")
        items.append(new)
        print(f"Added '{new}'.")
    elif choice == "2":
        if not items:
            print("The list is empty.")
        else:
            print("Current list:", items)
            remove = input("Enter the item to remove exactly: ")
            if remove in items:
                items.remove(remove)
                print(f"Removed '{remove}'.")
            else:
                print("That item is not in the list.")
    elif choice == "3":
        if not items:
            print("List is empty.")
        else:
            print("Items in your list:")
            for thing in items:       # basic for loop
                print("-", thing)
    elif choice == "4":
        print("You have", len(items), "item(s) in the list.")
    elif choice == "5":
        print("Goodbye!")
        break                        # exit
    else:
        print("Please enter a number from 1–5.")
