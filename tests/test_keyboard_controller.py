"""
Unit Test for Keyboard Controller
"""

import time

from automation.keyboard_controller import KeyboardController


def main():

    controller = KeyboardController()

    print("\n===================================")
    print("ASTRA Keyboard Controller Test")
    print("===================================")

    print("\nChoose an Option")
    print("1. Type Text")
    print("2. Press Enter")
    print("3. Press Tab")
    print("4. Ctrl + A")
    print("5. Ctrl + S")
    print("0. Exit")

    choice = input("\nEnter Choice : ")

    if choice == "1":

        text = input("\nEnter Text : ")

        print("\nYou have 5 seconds...")
        print("Open Notepad and click inside it.")

        time.sleep(5)

        success = controller.type_text(text)

        if success:
            print("\nTyping Completed.")
        else:
            print("\nTyping Failed.")

    elif choice == "2":

        print("\nYou have 5 seconds...")
        print("Open Notepad and click inside it.")

        time.sleep(5)

        success = controller.press_key("enter")

        if success:
            print("\nEnter Key Pressed.")
        else:
            print("\nFailed.")

    elif choice == "3":

        print("\nYou have 5 seconds...")
        print("Open Notepad and click inside it.")

        time.sleep(5)

        success = controller.press_key("tab")

        if success:
            print("\nTab Key Pressed.")
        else:
            print("\nFailed.")

    elif choice == "4":

        print("\nYou have 5 seconds...")
        print("Open Notepad, type some text and select nothing.")

        time.sleep(5)

        success = controller.hotkey("ctrl", "a")

        if success:
            print("\nCtrl + A Executed.")
        else:
            print("\nFailed.")

    elif choice == "5":

        print("\nYou have 5 seconds...")
        print("Open Notepad and click inside it.")

        time.sleep(5)

        success = controller.hotkey("ctrl", "s")

        if success:
            print("\nCtrl + S Executed.")
        else:
            print("\nFailed.")

    elif choice == "0":

        print("\nExiting Test...")

    else:

        print("\nInvalid Choice.")


if __name__ == "__main__":
    main()