import tclab
import time
import sys

# --- Configuration ---
# You can optionally specify the serial port if tclab fails to find it automatically.
# PORT = 'COM3' # Example port for Windows
# PORT = None # Keep as None to let tclab search for the device

# --- Main Program ---
try:
    print('Attempting to connect to TCLab...')
    # Initialize TCLab. It automatically handles the connection.
    # If a specific port is needed, use: a = tclab.TCLab(port=PORT)
    a = tclab.TCLab()
    
    # Check if connection was successful
    if a.connected:
        print(f'Successfully connected to TCLab at {a.port}')
        
        # Turn the LED On (100% brightness)
        print('LED On (100%)')
        a.LED(100)
        
        # Pause for 10 seconds
        print('Waiting for 10 seconds...')
        time.sleep(10.0)
        
        # Turn the LED Off
        print('LED Off')
        a.LED(0)
        
        # Close the connection
        a.close()
        print('Connection closed. Script finished.')
    else:
        print('Error: Could not find or connect to the TCLab device.')

except Exception as e:
    # This block catches errors during connection or operation
    error_message = f"An error occurred: {e}"
    print(error_message)

    # In an EXE file, the console closes quickly, so we pause to show the error
    if getattr(sys, 'frozen', False):
        input("\nPress Enter to exit and close this window...")