import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np

def create_grid(root):
    table_frame = tk.Frame(root)
    table_frame.pack()

    text_area = []
    for row in range(16):
        row_entries = []
        for col in range(6):
            entry = tk.Entry(table_frame, width=20, justify='center', state=tk.DISABLED)
            entry.grid(row=row, column=col, padx=1, pady=1)
            row_entries.append(entry)
        text_area.append(row_entries)
    
    return text_area

def update_grid(text_area, new_values):
    # Reshape new_values to 16 rows and 6 columns
    reshaped_values = np.array(new_values).reshape(16, 6).tolist()
    print(new_values)
    for row in range(16):
        for col in range(6):
            entry = text_area[row][col]
            entry_value = reshaped_values[row][col]
            
            entry.config(state=tk.NORMAL)  # Temporarily make the entry editable to update the value
            entry.delete(0, tk.END)
            entry.insert(0, str(entry_value))

            try:
                item_value_float = float(entry_value)
            except ValueError:
                item_value_float = 0.0 

            # Change color based on the value
            if item_value_float > 3.95:
                entry.config(bg='red')
            else:
                entry.config(bg='green')

            #entry.config(state=tk.DISABLED)  # Make the entry non-editable again

def main(csv_file_path):
    # Read the second row of the CSV file
    df = pd.read_csv(csv_file_path, header=None)
    list_values = df.iloc[1, :96].tolist()  # Get the first 96 values from the second row

    root = tk.Tk()
    text_area = create_grid(root)

    # Update the grid with the initial list of values
    update_grid(text_area, list_values)
    root.mainloop()

csv_file_path = r"C:\Users\VIVEK TANGRI\Desktop\Racing_project\AMSCelldata97 (1).csv"  # Update this with the path to your CSV file
main(csv_file_path)


""" def update_with_new_values():
        # New values for demonstration (replace this with actual new values)
        new_values = np.random.random(96) * 5
        update_grid(text_area, new_values)
    
    # Schedule the update with new values
    root.after(5000, update_with_new_values)  # Update after 5 seconds """