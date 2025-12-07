import tclab
import time
import numpy as np
import matplotlib.pyplot as plt

def run_p_controller(duration, T_sp, Kp):
    """
    Runs the P (Proportional) controller on the TCLab using the provided parameters,
    now including a temperature-based safety interlock.
    
    Args:
        duration (float): Total duration of the control run (seconds).
        T_sp (float): Setpoint temperature (°C).
        Kp (float): Proportional Gain.
    """
    # --- Controller and Experiment Parameters ---
    # Bias value (The steady-state heater power required for T1 at ambient conditions)
    OP_bias = 0.0 
    # Control interval (seconds)
    delta_t = 2.0
    
    # --- Safety Interlock Parameters ---
    T_max_safe = 75.0      # Temperature at which the heater is tripped OFF
    T_min_re_enable = 70.0 # Temperature at which the controller is re-enabled
    safety_trip_active = False # State flag for the safety system
    
    # --- Setup Variables and Data Logging ---
    n = int(duration / delta_t)
    t = np.zeros(n)
    T1 = np.zeros(n)
    T_sp_array = np.zeros(n)
    Q1 = np.zeros(n)
    
    lab = None # Initialize lab outside the try block

    # --- Initialize Plotting ---
    plt.figure(figsize=(10, 7))
    plt.ion() 
    plt.show()

    # Configure the Temperature Subplot
    ax1 = plt.subplot(2, 1, 1)
    ax1.set_ylabel('Temperature (°C)')
    line1, = ax1.plot(t, T1, 'r-', label='Temperature T1')
    line_sp, = ax1.plot(t, T_sp_array, 'k--', label='Setpoint $T_{sp}$')
    # Add a line to show the safety limit
    ax1.plot([0, duration], [T_max_safe, T_max_safe], 'r:', label=f'Safety Trip ({T_max_safe}°C)')
    ax1.legend(loc='best')
    ax1.set_xlim([0, duration])
    ax1.grid()
    plt.title(f'TCLab P Control with Safety Interlock (Kp={Kp}, $T_{{sp}}$={T_sp:.0f}°C)')

    # Configure the Heater Power Subplot
    ax2 = plt.subplot(2, 1, 2)
    ax2.set_ylabel('Heater Power (%)')
    ax2.set_xlabel('Time (s)')
    line2, = ax2.plot(t, Q1, 'b-', label='Heater Power Q1')
    ax2.legend(loc='best')
    ax2.set_xlim([0, duration])
    ax2.set_ylim([-5, 105])
    ax2.grid()
    plt.tight_layout()


    try:
        # --- Connect to TCLab ---
        print("Connecting to TCLab...")
        lab = tclab.TCLab()
        print("Connected to TCLab.")

        lab.Q1(0)
        lab.Q2(0)
        lab.LED(100)

        T1_initial = lab.T1
        print(f"Initial Temperature T1: {T1_initial:.2f} degC")
        
        # Set initial Y-axis limits now that T1_initial is defined
        y_min = min(T1_initial, T_sp, T_min_re_enable) - 5.0
        y_max = max(T1_initial, T_sp, T_max_safe) + 5.0
        ax1.set_ylim([y_min, y_max]) 

        # --- Main Control Loop ---
        for i in range(n):
            # Time logging
            t[i] = i * delta_t

            # Read temperature T1
            T1[i] = lab.T1
            T_sp_array[i] = T_sp

            # Calculate error (used only if not in trip state)
            error = T_sp - T1[i]

            # --- Safety Trip (Interlock) Logic ---
            if T1[i] >= T_max_safe:
                # Trip engaged: lock state
                safety_trip_active = True
                print(f"[TRIP] Safety Trip engaged at t={t[i]:.1f}s. Temperature hit {T1[i]:.2f}°C.")
            elif T1[i] < T_min_re_enable:
                # Re-enable: if the temperature drops below the re-enable point
                if safety_trip_active:
                     print(f"[RE-ENABLE] Safety Trip disengaged at t={t[i]:.1f}s. Temperature below {T_min_re_enable}°C.")
                safety_trip_active = False

            
            # --- Determine Controller Output (Q_calculated) ---
            if safety_trip_active:
                # If tripped, force Q1 to 0 and bypass controller calculation
                Q_output = 0.0
            else:
                # Calculate Proportional term
                P_term = Kp * error

                # Calculate Controller Output (OP)
                OP = OP_bias + P_term

                # --- Output Clamping ---
                Q_output = np.clip(OP, 0.0, 100.0)

            # Log and Apply the output to the heater
            Q1[i] = Q_output
            lab.Q1(Q1[i])
            
            # --- Update the Plot (REAL-TIME) ---
            line1.set_data(t[0:i+1], T1[0:i+1])
            line_sp.set_data(t[0:i+1], T_sp_array[0:i+1])
            line2.set_data(t[0:i+1], Q1[0:i+1])
            
            # Dynamic re-scaling (if necessary)
            if T1[i] > ax1.get_ylim()[1] or T1[i] < ax1.get_ylim()[0]:
                ax1.set_ylim([np.min(T1[0:i+1]) - 5, np.max(T1[0:i+1]) + 5])
                
            plt.draw() 
            plt.pause(0.05) 

            # Wait for the next control cycle
            time.sleep(delta_t - 0.05)

        last_10avg = np.mean(T1[-10:])
        steadystate_error = T_sp - last_10avg
        print(f"\nRun complete. Steady-state error: {steadystate_error:.2f} °C")

    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")

    finally: 
        # Ensure connection is closed and plot is shown
        print("Ensuring connection is closed and resources are released.")
        if lab is not None:
            try:
                lab.Q1(0) 
                lab.close()
            except:
                pass
        
        # Keep the final plot window open until the user closes it
        plt.ioff()
        plt.show()

# --- Main Execution Block for User Input ---
if __name__ == "__main__":
    
    print("--- TCLab P Controller Setup with Safety Interlock (75°C/70°C) ---")
    
    # 1. Input Duration
    while True:
        try:
            duration_input = input("Enter Experiment Time (s): ")
            duration_val = float(duration_input)
            if duration_val <= 0:
                print("Experiment time must be positive.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a numerical value for time.")
            
    # 2. Input Setpoint
    while True:
        try:
            tsp_input = input("Enter Set point (°C): ")
            tsp_val = float(tsp_input)
            break
        except ValueError:
            print("Invalid input. Please enter a numerical value for the set point.")
            
    # 3. Input Kp
    while True:
        try:
            kp_input = input("Enter Proportional Gain (Kp): ")
            kp_val = float(kp_input)
            break
        except ValueError:
            print("Invalid input. Please enter a numerical value for Kp.")

    print(f"\nRunning P controller for {duration_val:.0f}s with $T_{{sp}}$={tsp_val:.1f}°C, Kp={kp_val:.2f}")
    
    # Pass only three collected values to the P controller function
    run_p_controller(duration_val, tsp_val, kp_val)

    # Run "& "C:\Users\Alec\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\pyinstaller.exe" --onefile --console TCLab_Demo_PI.py"
    # in the terminal to create an executable version of this script.