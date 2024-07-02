import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog, simpledialog
import threading
import serial
import serial.tools.list_ports
import pandas as pd
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import signal
from PIL import Image, ImageTk
import numpy as np

data_list = []
data_saved = True
serial_connection = None
csv_file_path = None
csv_data = None
start_time = None
total_time = []
tsv_values = []
tsc_values = []
stop_threads = False
cell_values = [[] for _ in range(90)]
cell_averages = [0] * 90
columns_2 = []

DARK_BLUE = '#0D1B2A'
LIGHT_BLUE = '#1B263B'
RED = '#E63946'
YELLOW = '#FFD60A'
WHITE = '#F1FAEE'

def get_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def check_baud_rate(event):
    if selected_baud_rate.get() == "Other":
        custom_baud_rate = simpledialog.askinteger("Custom Baud Rate", "Enter baud rate:") #dialog box bana raha, agar other click kiya to get user baud_rate
        if custom_baud_rate:
            selected_baud_rate.set(custom_baud_rate)
        else:
            selected_baud_rate.set(baud_rates[0])

def connect():
    global stop_threads, cell_values, cell_averages
    stop_threads = False
    cell_values = [[] for _ in range(90)]
    cell_averages = [0] * 90
    if mode.get() == "Arduino":
        read_arduino_data()
    else:
        read_csv_data()

def read_arduino_data():
    port = selected_port.get()
    if port == "None":
        messagebox.showerror("Error", "No COM port selected or Arduino not connected")
        return

    try:
        baud_rate = int(selected_baud_rate.get())
        global serial_connection
        serial_connection = serial.Serial(port, baud_rate, timeout=1)
        connect_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        threading.Thread(target=process_data, args=(serial_connection,)).start()
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Could not open serial port {port}: {e}")
    except ValueError:
        messagebox.showerror("Error", "Invalid baud rate")

def read_csv_data():
    global csv_data
    if not csv_file_path:
        messagebox.showerror("Error", "No CSV file selected")
        return

    try:
        csv_data = pd.read_csv(csv_file_path, skiprows=1, usecols=lambda column_idx: column_idx <= 'GM')
        connect_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        threading.Thread(target=process_data, args=(csv_data,)).start()
    except Exception as e:
        messagebox.showerror("Error", f"Error reading CSV file: {e}")

def process_data(data_source):
    global data_saved, start_time, total_time, tsv_values, tsc_values, stop_threads
    start_time = time.time() * 1000
    total_time = []
    tsv_values = []
    tsc_values = []

    if isinstance(data_source, serial.Serial):
        while data_source.is_open and not stop_threads:
            data = data_source.readline().decode('utf-8').strip()
            if data:
                process_line(data)
    elif isinstance(data_source, pd.DataFrame):
        for index, row in data_source.iterrows():
            if stop_threads:
                break
            if not row.isna().any():
                data = ', '.join(map(str, row.values))
                process_line(data)
            time.sleep(0.1)

    connect_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def process_line(data):
    global start_time, total_time, tsv_values, tsc_values, data_saved, cell_values, cell_averages
    elapsed_time = (time.time() * 1000) - start_time
    #print(data_list)
    values = data.split(',')
    if len(values) > 192:
        if float(values[192]) > 100: #TSV value only noted if it is greater than 100V
            tsv = float(values[192])
            tsc = float(values[193])
            
            for i in range(90):
                try:
                    cell_values[i].append(float(values[i]))
                    cell_averages[i] = np.mean(cell_values[i]) #using numpy to calculate average of 90 values
                except ValueError:
                    pass

            total_time.append(elapsed_time)
            tsv_values.append(tsv)
            tsc_values.append(tsc)

        if plot_option.get() == "TSV Graph":
            plot_tsv_data(total_time, tsv_values)
        elif plot_option.get() == "TSC Graph":
            plot_tsc_data(total_time, tsc_values)
        elif plot_option.get() == "Cell Average":
            plot_cell_average_data()

    display_data(text_area_2, values[:96])
    #update_grid(text_area, list_values)
    data_list.append(data) #data ko data list mein daal diya
    data_saved = False

def plot_tsv_data(total_time, tsv_values):
    ax.clear()
    ax.scatter(total_time, tsv_values, color='blue', label="TSV")
    ax.plot(total_time, tsv_values, color='red', linestyle='-', linewidth=1)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("TSV")
    ax.set_title("TSV vs Time")
    ax.legend()
    canvas.draw()

def plot_tsc_data(total_time, tsc_values):
    ax.clear()
    ax.scatter(total_time, tsc_values, color='green', label="TSC")
    ax.plot(total_time, tsc_values, color='orange', linestyle='-', linewidth=1)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("TSC")
    ax.set_title("TSC vs Time")
    ax.legend()
    canvas.draw()

def plot_cell_average_data():
    ax.clear()
    x = range(1, 91)
    ax.scatter(x, cell_averages, color='purple', label="Cell Average")
    ax.set_xlabel("Cell Number")
    ax.set_ylabel("Average Voltage")
    ax.set_title("Cell Average Voltage")
    ax.legend()
    ax.set_xlim(1, 90)
    canvas.draw()

#text_area vaali jagah printing the values.
def display_data(area, new_values): 
    reshaped_values = np.array(new_values).reshape(16, 6).tolist()
    #print(new_values)
    for row in range(16):
        for col in range(6):
            entry = area[row][col]
            entry_value = reshaped_values[row][col]
            
            entry.config(state=tk.NORMAL)  #lagane ki zaroorat nahi hai
            entry.delete(0, tk.END)
            entry.insert(0, str(entry_value))

            try:
                item_value_float = float(entry_value)
            except ValueError:
                item_value_float = 0.0 

            # colour change kar rha
            if item_value_float > 3.95:
                entry.config(bg='red')
            else:
                entry.config(bg='green')

#grid banana
def create_grid(root):
    table_frame = tk.Frame(root)
    table_frame.pack()
    area = []
    for row in range(16):
        row_entries = []
        for col in range(6):
            entry = tk.Entry(table_frame, width=20, justify='center', state=tk.DISABLED)
            entry.grid(row=row, column=col, padx=1, pady=1)
            row_entries.append(entry)
        area.append(row_entries)
    
    return area
#select_csv file accesses your computer and check ki flie extension tumhara .csv hai ki nahi
def select_csv_file():
    global csv_file_path
    csv_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if csv_file_path:
        messagebox.showinfo("File Selected", f"Selected file: {csv_file_path}")

def save_data_as():
    if not data_list:
        messagebox.showinfo("Info", "No data to save")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    if file_path:
        df = pd.DataFrame(data_list, columns=["Data"])
        df.to_excel(file_path, index=False)
        global data_saved
        data_saved = True
        messagebox.showinfo("Info", "Data saved successfully")

def clear_data():
    global data_saved, cell_values, cell_averages
    if not data_saved:
        if messagebox.askyesno("Unsaved Data", "You have unsaved data. Do you want to save before clearing?"):
            save_data_as()
            if not data_saved:
                return
    text_area.delete(1.0, tk.END)
    """ for item in tree.get_children():
        tree.delete(item) """
    data_list.clear()
    cell_values = [[] for _ in range(90)]
    cell_averages = [0] * 90
    data_saved = True
    ax.clear()
    canvas.draw()

def stop_data_capture():
    global serial_connection, stop_threads
    stop_threads = True
    stop_button.config(state=tk.DISABLED)
    if serial_connection is not None:
        serial_connection.close()
    connect_button.config(state=tk.NORMAL)

#file band karte samay ye dikhega 
def on_closing():
    global data_saved, stop_threads, serial_connection
    stop_threads = True
    if not data_saved:
        if messagebox.askyesno("Unsaved Data", "You have unsaved data. Do you want to save before exiting?"):
            save_data_as()
            if not data_saved:
                return
    if serial_connection is not None and serial_connection.is_open:
        serial_connection.close()
    time.sleep(1)
    root.destroy()
    os.kill(os.getpid(), signal.SIGTERM)

def update_mode():
    if mode.get() == "Arduino":
        port_frame.pack(fill=tk.X, pady=10)
        baud_frame.pack(fill=tk.X, pady=10)
        csv_button.pack_forget() #agar selected mode arduino hai toh csv button hatao
    else:
        port_frame.pack_forget() 
        baud_frame.pack_forget()
        csv_button.pack(fill=tk.X, pady=10) 

def update_graph_visibility(event):
    if plot_option.get() in ["TSV Graph", "TSC Graph", "Cell Average"]:
        canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
    else:
        canvas.get_tk_widget().pack_forget()

#this is the GUI window declaration
root = tk.Tk()
root.title("F1 Student Racing Team Data Acquisition")
root.configure(bg=DARK_BLUE)

#tells ki kitna badi screen is to be opened for showing
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height-40}")

image = Image.open("logo.png")
image = image.resize((300, 120), Image.LANCZOS)
logo_img = ImageTk.PhotoImage(image)

#the following 4 lines add the fucking logo in out GUI
image_label = tk.Label(root, image=logo_img)
image_label.image = logo_img
image_label.pack(side=tk.TOP, pady=20)
image_label.config(bg=DARK_BLUE, fg=WHITE , font=('Arial', 14, 'bold'))

#basically made 3 frames of some sort
main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=20)
main_frame.config(bg=DARK_BLUE)

#this is the part of the window jaha pe saare options visible hai
left_frame = tk.Frame(main_frame, width=300)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
left_frame.config(bg=DARK_BLUE)

#kuch chudaap hai
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
right_frame.config(bg=DARK_BLUE)

#Select mode vaala part jo hai
mode_frame = tk.Frame(left_frame)
mode_frame.pack(fill=tk.X, pady=10)
mode_frame.config(bg=DARK_BLUE)

#select mode vaala button
mode_label = tk.Label(mode_frame, text="Select Mode:")
mode_label.pack(anchor='w', pady=(0, 5))
mode_label.config(bg=DARK_BLUE, fg=WHITE , font=('Arial', 14, 'bold'))

#basically, used for writing "arduino"
mode = tk.StringVar()
mode.set("Arduino")

#arduino naam ka radio button bana raha ye code
arduino_radio = tk.Radiobutton(mode_frame, text="Arduino", variable=mode, value="Arduino", command=update_mode)
arduino_radio.pack(anchor='w')
arduino_radio.config(bg=DARK_BLUE,fg=WHITE, selectcolor=RED,activebackground=DARK_BLUE,activeforeground=YELLOW,font=('Arial', 12))

#CSV naam ka radio button bana raha
csv_radio = tk.Radiobutton(mode_frame, text="CSV", variable=mode, value="CSV", command=update_mode)
csv_radio.pack(anchor='w')
csv_radio.config(bg=DARK_BLUE,fg=WHITE, selectcolor=RED,activebackground=DARK_BLUE,activeforeground=YELLOW,font=('Arial', 12))

#usb ports of device ka info
com_ports = get_com_ports()
selected_port = tk.StringVar()
selected_port.set(com_ports[0] if com_ports else "None")

#Select com port vaala part getting defined here
port_frame = tk.Frame(left_frame)
port_frame.config(bg=DARK_BLUE)
port_frame.pack(fill=tk.X, pady=10)

port_label = tk.Label(port_frame, text="Select COM Port:")
port_label.pack(anchor='w', pady=(0, 5))
port_label.config(bg=DARK_BLUE, fg=WHITE , font=('Arial', 14, 'bold'))

#corresponding drop down box being made
port_dropdown = ttk.Combobox(port_frame, textvariable=selected_port, values=com_ports, font=('Arial', 12))
port_dropdown.pack(fill=tk.X)

baud_rates = [9600, 14400, 19200, 38400, 57600, 115200, "Other"]
selected_baud_rate = tk.StringVar()
selected_baud_rate.set(baud_rates[0]) # default baud_rate set hui idhar


baud_frame = tk.Frame(left_frame) #tk.frame(left_frame) bas ye idea de raha kidhar banana apna option baud_rate vala
baud_frame.pack(fill=tk.X, pady=10)
baud_frame.config(bg=DARK_BLUE)

baud_rate_label = tk.Label(baud_frame, text="Select Baud Rate:")
baud_rate_label.pack(anchor='w', pady=(0, 5))
baud_rate_label.config(bg=DARK_BLUE, fg=WHITE , font=('Arial', 14, 'bold')) #bg fg is background and fore ground, fore ground is above back ground obv

baud_rate_dropdown = ttk.Combobox(baud_frame, textvariable=selected_baud_rate, values=baud_rates, font=('Arial', 12))
baud_rate_dropdown.pack(fill=tk.X)
baud_rate_dropdown.bind("<<ComboboxSelected>>", check_baud_rate) #check_baud rate vala tab ayega jab other click kar diya

#csv select button
csv_button = tk.Button(left_frame, text="Select CSV File", command=select_csv_file)
csv_button.pack(fill=tk.X, pady=10)
csv_button.pack_forget() 
csv_button.config(bg=LIGHT_BLUE,fg=WHITE,activebackground=RED,activeforeground=WHITE, font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=20,pady=10,cursor="hand2")

#ye next teen button are quite obv
connect_button = tk.Button(left_frame, text="Connect", command=connect)
connect_button.pack(fill=tk.X, pady=10)
connect_button.config(bg=LIGHT_BLUE,fg=WHITE,activebackground=RED,activeforeground=WHITE, font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=20,pady=10,cursor="hand2")

stop_button = tk.Button(left_frame, text="Stop Data Capture", command=stop_data_capture, state=tk.DISABLED)
stop_button.pack(fill=tk.X, pady=10)
stop_button.config(bg=LIGHT_BLUE,fg=WHITE,activebackground=RED,activeforeground=WHITE, font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=20,pady=10,cursor="hand2")

clear_button = tk.Button(left_frame, text="Clear", command=clear_data)
clear_button.pack(fill=tk.X, pady=10)
clear_button.config(bg=LIGHT_BLUE,fg=WHITE,activebackground=RED,activeforeground=WHITE, font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=20,pady=10,cursor="hand2")

#graph plotting ka options dikha raha
plot_option = tk.StringVar()
plot_option.set("None")

graph_frame = tk.Frame(left_frame)
graph_frame.config(bg=DARK_BLUE)
graph_frame.pack(fill=tk.X, pady=10)

graph_label = tk.Label(graph_frame, text="Graph Display:")
graph_label.pack(anchor='w', pady=(0, 5)) #When you use anchor='w', you are specifying that the widget should be anchored to the west (left) side of its allocated space.
graph_label.config(bg=DARK_BLUE, fg=WHITE , font=('Arial', 14, 'bold'))

#combobox makes dropb down menu
graph_options = ttk.Combobox(graph_frame, textvariable=plot_option, values=["None", "TSV Graph", "TSC Graph", "Cell Average"], state="readonly", font=('Arial', 12))
graph_options.pack(fill=tk.X)
graph_options.bind("<<ComboboxSelected>>", update_graph_visibility)

text_area = scrolledtext.ScrolledText(right_frame, wrap=tk.NONE, font=('Courier', 12))
text_area.pack(expand=True, fill=tk.BOTH, pady=(0, 10))
text_area_2 = create_grid(text_area)

#main area jaha data likh ke aa raha hai
""" text_area_scroll_x = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=text_area.xview)
text_area_scroll_x.pack(fill=tk.X)
text_area['xscrollcommand'] = text_area_scroll_x.set
text_area.config(bg=RED, fg=WHITE) """


columns_2 = ("S1C1", "S1c2", "s1C3", "S1C4","S1C5", "S1c6", "s1C7", "S1C8","S1C9", "S1c10", "s1C11", "S1C12","S1C13", "S1c14", "s1C15","S2C1", "S2c2", "s2C3", "S2C4","S2C5", "S2c6", "s2C7", "S2C8","S2C9", "S2c10", "s2C11", "S2C12","S2C13", "S2c14", "s2C15","S3C1", "S3c2", "s3C3", "S3C4","S3C5", "S3c6", "s3C7", "S3C8","S3C9", "S3c10", "s3C11", "S3C12","S3C13", "S3c14", "s3C15","S4C1", "S4c2", "s4C3", "S4C4","S4C5", "S4c6", "s4C7", "S4C8","S4C9", "S4c10", "s4C11", "S4C12","S4C13", "S4c14", "s4C15","S5C1", "S5c2", "s5C3", "S5C4","S5C5", "S5c6", "s5C7", "S5C8","S5C9", "S5c10", "s5C11", "S5C12","S5C13", "S5c14", "s5C15","S6C1", "S6c2", "s6C3", "S6C4","S6C5", "S6c6", "s6C7", "S6C8","S6C9", "S6c10", "s6C11", "S6C12","S6C13", "S6c14", "s6C15","S7C1", "S7c2", "s7C3", "S7C4","S7C5", "S7c6","S1t1", "S1t2", "s1t3", "S1t4","S1t5", "S1t6t", "s1t7", "S1t8","S1t9", "S1t10", "s1t11", "S1t12","S1t13", "S1t14", "s1t15","S2t1", "S2t2", "s2t3", "S2t4","S2t5", "S2t6", "s2t7", "S2t8","S2t9", "S2t10", "s2t11", "S2t12","S2t13", "S2t14", "s2t15","S3t1", "S3t2", "s3t3", "S3t4","S3t5", "S3t6", "s3t7", "S3t8","S3t9", "S3t10", "s3t11", "S3t12","S3t13", "S3t14", "s3t15","S4t1", "S4t2", "s4t3", "S4t4","S4t5", "S4t6", "s4t7", "S4t8","S4t9", "S4t10", "s4t11", "S4t12","S4t13", "S4t14", "s4t15","S5t1", "S5t2", "s5t3", "S5t4","S5t5", "S5t6", "s5t7", "S5t8","S5t9", "S5t10", "s5t11", "S5t12","S5t13", "S5t14", "s5t15","S6t1", "S6t2", "s6t3", "S6t4","S6t5", "S6t6", "s6t7", "S6t8","S6t9", "S6t10", "s6t11", "S6t12","S6t13", "S6t14", "s6t15","S7t1", "S7t2", "s7t3", "S7t4","S7t5", "S7t6", "TSV", "TSC", "TSP")
style = ttk.Style()
style.configure("Custom.Treeview", 
                background="#0D1B2A", 
                foreground="red", 
                fieldbackground="#0D1B2A",
                rowheight=25,
                font=('Arial', 12))
""" tree = ttk.Treeview(text_area, columns=columns_2, show="headings", style="Custom.Treeview")
for col in columns_2:
    tree.heading(col, text=col)
    tree.column(col, width=70) """

""" h_scrollbar = ttk.Scrollbar(text_area, orient=tk.HORIZONTAL, command=tree.xview)
tree.configure(xscrollcommand=h_scrollbar.set)
tree.pack(expand=True, fill=tk.BOTH)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
 """
table_frame = tk.Frame(text_area)
table_frame.pack()
s = ttk.Style()
s.configure('MyStyle.Treeview', rowheight=25)
tree = ttk.Treeview(table_frame, height=1, show="tree", columns=("0"), style='MyStyle.Treeview')




tree.tag_configure('GREEN', background='#008000', foreground='white')
tree.tag_configure('RED', background='red', foreground='white')

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_facecolor(DARK_BLUE)
fig.patch.set_facecolor(DARK_BLUE)
ax.tick_params(colors=WHITE)
ax.xaxis.label.set_color(WHITE)
ax.yaxis.label.set_color(WHITE)
ax.title.set_color(WHITE)
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Value")
ax.set_title("Data vs Time")
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
canvas.draw()

canvas.get_tk_widget().pack_forget()

menu = tk.Menu(root)
menu.config(bg=DARK_BLUE, fg=WHITE)
root.config(menu=menu)
file_menu = tk.Menu(menu, tearoff=0)
file_menu.config(bg=DARK_BLUE, fg=WHITE)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save As", command=save_data_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()