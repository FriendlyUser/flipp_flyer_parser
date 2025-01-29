import subprocess

def run_all():
    # args = ["saveon", "walmart", "superstore", "loblaws"]
    args = ["walmart", "superstore", "loblaws"]
    for arg in args:
        print(f"Running main.py with argument: {arg}")
        # subprocess.run blocks until the command finishes
        subprocess.run(["python", "main.py", "-t", arg], check=True)
        print(f"Done running with argument: {arg}")
        print("-----------------------------------")

    print("All processes have finished.")

if __name__ == "__main__":
    run_all()
