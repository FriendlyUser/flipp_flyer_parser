import subprocess
import time

def run_all():
    # args = ["walmart", "superstore", "loblaws", "saveon"]
    args = ["superstore", "loblaws", "saveon"]
    # args = ["loblaws", "saveon"]
    # args = ["superstore", "loblaws"]
    for arg in args:
        print(f"Running main.py with argument: {arg}")
        # subprocess.run blocks until the command finishes
        subprocess.run(["python", "main.py", "--type", arg], check=True)
        print(f"Done running with argument: {arg}")
        print("-----------------------------------")
        time.sleep(10)

    print("All processes have finished.")

if __name__ == "__main__":
    run_all()
