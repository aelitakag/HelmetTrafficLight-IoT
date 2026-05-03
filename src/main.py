from server import app

# start the server

if __name__ == "__main__":
    print("[INFO] Starting main server...")

    # allow external devices (like Raspberry Pi) to connect
    app.run(host="0.0.0.0", port=5000, debug=False)