
import time

def count_to_five():
    i = 0
    while i < 5:
        print(i)
        # Forgot to increment i!
        time.sleep(0.1)

if __name__ == "__main__":
    count_to_five()
