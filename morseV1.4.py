import RPi.GPIO as GPIO
import time
import sys
import select
import termios
import tty

# GPIO setup
BUTTON_PIN = 26
BUZZER_PIN = 12 

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Morse code dictionary
MORSE_CODE_DICT = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", "-----": "0", ".----": "1", "..---": "2",
    "...--": "3", "....-": "4", ".....": "5", "-....": "6", "--...": "7",
    "---..": "8", "----.": "9"
}

# Function to play a tone on the buzzer
def play_tone(frequency, duration):
    pwm = GPIO.PWM(BUZZER_PIN, frequency)
    pwm.start(50)
    time.sleep(duration)
    pwm.stop()

def record_morse():
    # Set the terminal to cbreak mode for immediate key input (non-canonical)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    
    print("Recording Morse Code. Short press = dot, long press = dash.")
    print("Press SPACE to end a letter, '\\' to end a word, and 's' to send & play.")

    words = []         # List to store words; each word is a list of letter codes.
    current_word = []  # Current word (list of letters)
    current_letter = []  # Current letter (list of dots/dashes)

    try:
        while True:
            # Non-blocking check for keyboard input
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key == ' ':
                    # End of a letter
                    if current_letter:
                        letter_code = "".join(current_letter)
                        current_word.append(letter_code)
                        current_letter = []
                        print(" ", end="", flush=True)  # Visual separator for letters
                    continue
                elif key == '\\':
                    # End of a word
                    if current_letter:
                        letter_code = "".join(current_letter)
                        current_word.append(letter_code)
                        current_letter = []
                    if current_word:
                        words.append(current_word)
                        current_word = []
                        print("   /   ", end="", flush=True)  # Visual separator for words
                    continue
                elif key.lower() == 's':
                    # End recording and send the message
                    if current_letter:
                        letter_code = "".join(current_letter)
                        current_word.append(letter_code)
                        current_letter = []
                    if current_word:
                        words.append(current_word)
                    break

            # Check for button press (record dot or dash)
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                start_time = time.time()
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    time.sleep(0.01)
                duration = time.time() - start_time

                # Interpret duration as dot or dash
                if duration > 0.5:
                    current_letter.append("-")
                    print("-", end="", flush=True)
                elif duration > 0.05:
                    current_letter.append(".")
                    print(".", end="", flush=True)
                time.sleep(0.1)  # Debounce delay

    finally:
        # Always restore the terminal settings when done
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return words

# Main loop
try:
    while True:
        print("\n\nMorse Code Trainer")
        print("1. Record, Display & Play Morse Code")
        print("2. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            # Record the Morse code input from the user.
            words = record_morse()

            # Display the recorded Morse code.
            print("\n\nRecorded Morse Code:")
            for word in words:
                for letter in word:
                    print(letter, end=" ")
                print("   ", end="")
            print("\n")

            # Decode and print the corresponding text.
            print("Decoded Message:")
            for word in words:
                decoded_word = ""
                for letter in word:
                    decoded_word += MORSE_CODE_DICT.get(letter, "?")
                print(decoded_word, end=" ")
            print("\n")

            # Play the Morse code via the buzzer.
            print("Playing Morse Code...")
            for word in words:
                for letter in word:
                    for symbol in letter:
                        if symbol == ".":
                            play_tone(800, 0.2)  # Dot tone
                        elif symbol == "-":
                            play_tone(600, 0.5)  # Dash tone
                        time.sleep(0.2)  # Pause between symbols
                    time.sleep(0.5)  # Pause between letters
                time.sleep(0.8)  # Pause between words

        elif choice == "2":
            print("Exiting...")
            break

except KeyboardInterrupt:
    print("\nInterrupted!")

finally:
    GPIO.cleanup()
