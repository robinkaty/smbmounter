#!/usr/bin/env python3
# Notes:
# if run from command line the mounts file will be the scriptname + .txt IE: smbMounter.py.txt
# if run from Platypus, the script name is always "script.txt" I need to find a way to 
# make these to the same.
# Added mac sounds to the automount function
# Added a display box to cache messages created during the auto_mount and display them after
# the main grid is displayed.
# refactored some code in the mount and automount functions
# consolidated the  mounting to  mount_network_share
#  brew intall python3
#  brew install python-tk@3.11
#  brew install python-gdbm@3.11
#  pip3 install tk

from typing import Union
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess
import os
import sys
#from tkinter import ttk
import tkinter.font as tkfont
import platform

messages = []


def show_message(*args, **kwargs):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Make the window always on top

    # Forward all arguments and keyword arguments to messagebox.showinfo
    result = messagebox.showinfo(*args, **kwargs)
    
    root.destroy()  # Destroy the main window when done

    return result  # Return the result from messagebox.showinfo

# Usage example:
#show_message("Title", "Your message here")


def beephappy():
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(1998, 500) # type: ignore
    elif platform.system() == "Darwin":
        import os

        os.system("afplay /System/Library/Sounds/Tink.aiff")
    elif platform.system() == "Linux":
        import os

        os.system("beep")

def get_supported_systems_for_protocol(configurations, protocol):
    # Check if the specified protocol is supported
#    if protocol not in configurations:
#        raise ValueError(f"Unsupported protocol: {protocol}")

    # Get the systems that support the specified protocol
    supported_systems = list(configurations[protocol.lower()].keys())
    return ", ".join(supported_systems)

def mount_network_share(share, server_name, mount_point, protocol, user, password, auto_mount=False):
    system = platform.system().lower()

    # Define configurations for different protocols and operating systems
    configurations = {
        "smb": {
            "windows": (f"net use {mount_point} \\\\{server_name}\\{share} {password} /user:{user}\\{password}" if user else f"net use {mount_point} \\\\{server_name}\\{share}"),
            "darwin": (f"mount -t smbfs //{user}:{password}@{server_name}/{share} {mount_point}" if user and password else f"mount -t smbfs //{server_name}/{share} {mount_point}"),
            "linux": (f"mount -t cifs //{share} {mount_point} -o username={user},password={password}" if user and password else f"mount -t cifs //{server_name}/{share} {mount_point}")
        },
        "nfs": {   
            "darwin": f"mount -t nfs -o vers=4.0 {server_name}:{share} {mount_point}",
            "linux": f"mount -t nfs {server_name}:{share} {mount_point}"
        }
    }

    # Check if the protocol is supported
    if protocol.lower() not in configurations:
         # Get the keys (protocols) from the top-level dictionary
        supported_protocols = list(configurations.keys())
        # Create a comma-separated string of supported protocols
        protocols_str = ", ".join(supported_protocols)     
        raise ValueError(f"Unsupported protocol {protocol}. Supported protocols are: {protocols_str}.")

    # Check if the system is supported for the given protocol
    #supported_systems = get_supported_systems_for_protocol(configurations, protocol)


    if system not in configurations[protocol.lower()]:
        # Get the systems for the specified protocol
        # Get the values to the left of ":" (e.g., "darwin", "linux")
        supported_systems = get_supported_systems_for_protocol(configurations, protocol)
        raise ValueError(f"Unsupported system {system}. Supported Systems are: {supported_systems}.")
        #raise NotImplementedError(f"Unsupported operating system: {system}")

    mount_command = configurations[protocol.lower()][system]

    try:
        subprocess.run(mount_command, shell=True, check=True)
        #print(f"{protocol.upper()} share mounted at {mount_point}")
    except subprocess.CalledProcessError as e:
        #show_message(f"{mount_command} failed with Error: {e}")
        if e.returncode == 64:
            error_str = f"The Network share is no longer availble {share} : {e}"
        else:
            error_str = f"{e}"

        raise SystemError (f"Error: {error_str}") from e


# Example usage:
# mount_network_share("smb://server/share", "/mnt/mountpoint", "smb", "username", "password")
# mount_network_share("nfs://server/share", "/mnt/mountpoint", "nfs")

def beepsad():
    if platform.system() == "Windows":
        import winsound

        winsound.Beep(1000, 200) # type: ignore
        winsound.Beep(500, 200) # type: ignore
        winsound.Beep(1000, 200) # type: ignore
        winsound.Beep(500, 200) # type: ignore
        winsound.Beep(1000, 200) # type: ignore
    elif platform.system() == "Darwin":
        import os

        os.system("afplay /System/Library/Sounds/Basso.aiff")
    elif platform.system() == "Linux":
        import os

        os.system("beep")
        os.system("beep")
        os.system("beep")



class SmbManager(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master # type: ignore
        self.master.protocol("WM_DELETE_WINDOW", self.save_on_exit)
        self.grid(sticky="nsew")
        self.create_widgets()
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)        
        self.pack(fill='both', expand=True)
        self.after(100, self.display_messages)  # Display messages after 100 mili second


    def add_message(self, message):
        messages.append(message)

    def display_messages(self):
        message_text = "\n".join(messages)
        longest_message_length = max(len(message) for message in messages)

        # Create a Toplevel window for the pop-up text box
        top = tk.Toplevel(self.master)
        top.title("Messages")

        # Create a Text widget to display the messages
        text_box = tk.Text(top, width=longest_message_length + 5, height=10)

#        text_box = ttk.Text(top, width=50, height=10)
        text_box.insert(tk.END, message_text)
        text_box.configure(state='disabled')  # Make the text box read-only
        text_box.pack(fill=tk.BOTH, expand=True)  # Pack the Text widget to fill the available space

        # Create a Scrollbar widget
        scrollbar = tk.Scrollbar(top, command=text_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the Text widget to use the Scrollbar
        text_box.configure(yscrollcommand=scrollbar.set)

        # After 5 seconds, destroy the top-level window
        self.after(5000, top.destroy)

    def get_max_column_lengths(self,file_path):
        max_lengths = {column: 0 for column in ["Share", "Server", "Username", "Password", "MountPoint", "AutoMount","FSTYPE"]}


        with open(file_path, "r") as file:
            for line in file:
                values = line.strip().split(",")
                for column, value in zip(max_lengths.keys(), values):
                    max_lengths[column] = max(max_lengths[column], len(value))
        
        return max_lengths



    def create_widgets(self):
        self.treeview = ttk.Treeview(self )
#        self.treeview.grid(row=0,columnspan=1, padx=5,  pady=3, sticky="ew")
        max_lengths = self.get_max_column_lengths(file_path)
        self.treeview.grid(row=0, column=0, padx=5, pady=3, sticky="nsew")

        self.treeview['show']='headings'



        self.treeview["columns"] = ("Share", "Server", "Username", "Password", "MountPoint", "AutoMount","FSTYPE")
        self.treeview.heading("Share", text="Share")
        self.treeview.heading("Server", text="Server")
        self.treeview.heading("Username", text="Username")
        self.treeview.heading("Password", text="Password")
        self.treeview.heading("MountPoint", text="MountPoint")
        self.treeview.heading("AutoMount", text="AutoMount")
        self.treeview.heading("FSTYPE", text="FSTYPE")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.set_column_widths()


        self.treeview.bind("<Double-1>", self.handle_double_click)


        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.treeview.yview)
        self.scrollbar.grid(row=0, column=3, sticky="ns")
        self.treeview.configure(yscrollcommand=self.scrollbar.set)
#test
        self.share_label = ttk.Label(self, text="Share Name:")
        self.share_label.grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.share_entry = ttk.Entry(self, width=50 )
        self.share_entry.grid(row=1, column=0, padx=100, pady=3, sticky="w")



        self.server_label = ttk.Label(self, text="Server Name:")
        self.server_label.grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.server_entry = ttk.Entry(self, width=50)
        self.server_entry.grid(row=2, column=0, padx=100, pady=3, sticky="w")

        self.user_label = ttk.Label(self, text="Username:")
        self.user_label.grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.user_entry = ttk.Entry(self, width=50)
        self.user_entry.grid(row=3, column=0, padx=100, pady=3, sticky="w")

        self.password_label = ttk.Label(self, text="Password:")
        self.password_label.grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.password_entry = ttk.Entry(self, width=50, show="*")
        self.password_entry.grid(row=4, column=0, padx=100, pady=3, sticky="w")


        self.mount_label = ttk.Label(self, text="MountPoint:\n(Dbl-clk)",foreground="blue",wraplength=80,justify="left")
        self.mount_label.grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.mount_entry = ttk.Entry(self, width=50)
        self.mount_entry.grid(row=5, column=0, padx=100, pady=3, sticky="w")
        self.mount_entry.bind("<Double-Button-1>", lambda event: self.browse_mount())

        


        self.auto_mount_label = ttk.Label(self, text="Auto-mount:")
        self.auto_mount_label.grid(row=6, column=0, padx=5, pady=3, sticky="w")
        self.auto_mount_entry = ttk.Entry(self, width=50)
        self.auto_mount_entry.grid(row=6, column=0, padx=100, pady=3, sticky="w")


        self.fstype_label = ttk.Label(self, text="FSTYPE:")
        self.fstype_label.grid(row=7, column=0, padx=5, pady=3, sticky="w")
        self.fstype_entry = ttk.Entry(self, width=50)
        self.fstype_entry.grid(row=7, column=0, padx=100, pady=3, sticky="w")        


        self.add_button = ttk.Button(self, text="Add Mount", command=self.add_mount)
        self.add_button.grid(row=9, column=0, padx=5, pady=3, sticky="w")


        self.edit_button = ttk.Button(self, text="Edit Mount", command=self.edit_mount)
        self.edit_button.grid(row=9, column=0, padx=150, pady=3, sticky="w")        

        self.delete_button = ttk.Button(self, text="Delete Mount", command=self.delete_mount)
        self.delete_button.grid(row=9, column=0, padx=300, pady=3, sticky="w")

        self.mount_button = ttk.Button(self, text="Mount", command=self.mount)
        self.mount_button.grid(row=10, column=0, padx=5, pady=3, sticky="w")

        self.save_button = ttk.Button(self, text="Save Mounts", command=self.save_mounts)
        self.save_button.grid(row=10, column=0,  padx=150, pady=3, sticky="w")

        self.duplicate_button = ttk.Button(self, text="Duplicate Mount", command=self.duplicate_mount)
        self.duplicate_button.grid(row=10, column=0, padx=300, pady=3, sticky="w")



        self.unmount_button = ttk.Button(self, text="Unmount", command=self.unmount)
        self.unmount_button.grid(row=11, column=0, padx=5, pady=3, sticky="w")

        self.test_button = ttk.Button(self, text="Test", command=self.test)
        self.test_button.grid(row=11, column=0, padx=150, pady=3, sticky="w")




        self.load_mounts()

    def set_column_widths(self):
        # Calculate the maximum width among the column names
        max_width = max(self.measure_text(column_name) for column_name in self.treeview["columns"])
        max_lengths = self.get_max_column_lengths(file_path)
        # Loop over the column IDs and adjust the widths
        for column_id in self.treeview["columns"]:
            column_name = self.treeview.heading(column_id)["text"]
            column_width = self.treeview.column(column_id, option="width")
            column_minwidth = self.treeview.column(column_id, option="minwidth")
            # Calculate the desired width based on the size of the column name

            desired_width = max ( len(column_name), max_lengths[column_name]) * 10
            self.treeview.column(column_id, width=desired_width,minwidth=desired_width,stretch=True) 
            
            
    def measure_text(self, text):
        return len(text) * 5


    def handle_double_click(self, event):
        if selection := self.treeview.selection():
            self.edit_mount()


    def browse_mount(self):
        if mount_path := filedialog.askdirectory():
            self.mount_entry.delete(0,  tk.END)
            self.mount_entry.insert(0, mount_path)

    def add_mount(self):
        values = []
        share = self.share_entry.get()
        server_name = self.server_entry.get()
        user = self.user_entry.get()
        password = self.password_entry.get()
        mount_point = self.mount_entry.get()
        auto_mount = self.auto_mount_entry.get()
        fstype = self.fstype_entry.get()


        self.treeview.insert("", "end",values=(share, server_name, user, password, mount_point, auto_mount,fstype))
        self.clear_entries()

    def edit_mount(self):
        if selection := self.treeview.selection():
            item = self.treeview.item(selection) # type: ignore
            values = item["values"]

            self.share_entry.delete(0,  tk.END)
            self.share_entry.insert(0, values[0])

            self.server_entry.delete(0,  tk.END)
            self.server_entry.insert(0, values[1])

            self.user_entry.delete(0,  tk.END)
            self.user_entry.insert(0, values[2])

            self.password_entry.delete(0,  tk.END)
            self.password_entry.insert(0, values[3])

            self.mount_entry.delete(0,  tk.END)
            self.mount_entry.insert(0, values[4])

            self.auto_mount_entry.delete(0,  tk.END)
            self.auto_mount_entry.insert(0, values[5])

            self.fstype_entry.delete(0,  tk.END)
            self.fstype_entry.insert(0, values[6])          

            self.delete_mount()
        else:
            messagebox.showerror("Edit", "Please select a mount to edit.")



    def delete_mount(self):
        if selection := self.treeview.selection():
            self.treeview.delete(selection) # type: ignore
        else:
            messagebox.showerror("Delete", "Please select a mount to delete.")

    def duplicate_mount(self):
        if selection := self.treeview.selection():
            item = self.treeview.item(selection) # type: ignore
            values = item["values"]
            self.treeview.insert("", "end", text="", values=values)
        else:
            messagebox.showerror("Duplicate", "Please select a mount to duplicate.")




    def do_auto_mount(self, values):
        share, server_name, user, password, mount_point, auto_mount, fstype = values.split(",")

        if os.path.ismount(mount_point):
            self.add_message(f"The MountPoint directory '{mount_point}' for '{share}' already exists and is mounted.")
            beephappy()
            #os.system('afplay /System/Library/Sounds/Tink.aiff')
            return

        if not os.path.exists(mount_point):
            if create_dir := messagebox.askyesno(
                "Mount",
                f"The MountPoint directory '{mount_point}' for '{share}' does not exist. Do you want to create it?",
            ):
                try:
                    os.makedirs(mount_point)
                except Exception:
                    #os.system('afplay /System/Library/Sounds/Basso.aiff')
                    beepsad()
                    return

        if not os.path.exists(mount_point):
            #os.system('afplay /System/Library/Sounds/Basso.aiff')
            beepsad()
            return
        try:
            mount_network_share(share, server_name, mount_point, fstype, user, password, auto_mount=True)
            beephappy()
            #messagebox.showinfo("Mount", f"The mount for '{server_name}:{share}' to '{mount_point}' was successful.")
            self.add_message(f"The {fstype} mount for '{server_name}:{share} {mount_point}' was successful.")
        except ValueError as e:
            #self.add_message(f"There was an error mounting {share} : {e}.")
            self.add_message(f"The {fstype} mount for '{server_name}:{share}' failed with error: {e}.")
            beepsad()
        except SystemError:
            messagebox.showerror(f"{e}")

        except Exception:
            #os.system('afplay /System/Library/Sounds/Basso.aiff')
            beepsad()
            self.add_message(f"The {fstype} mount for '{server_name}:{share}' failed with error: {e}.")
            #messagebox.showerror("Mount", f"The mount for '{server_name}:{share}' to '{mount_point}' failed with an error: ")


        
    def mount(self):
        selection = self.treeview.selection()
        if not selection:
            messagebox.showerror("Mount", "Please select a mount to execute.")
            return

        item = self.treeview.item(selection)  # type: ignore
        values = item["values"]
        share, server_name, user, password, mount_point, auto_mount, fstype = values

        if os.path.ismount(mount_point):
            beephappy()
            #show_message("Mount", f"The directory '{mount_point}' is already mounted.")
            messagebox.showinfo("Mount", f"The directory '{mount_point}' is already mounted.")
            return

        if not os.path.exists(mount_point):
            if create_dir := messagebox.askyesno(
                "Mount",
                f"The MountPoint directory '{mount_point}' for '{share}' does not exist. Do you want to create it?",
            ):
                try:
                    os.makedirs(mount_point)
                except Exception:
                    #os.system('afplay /System/Library/Sounds/Basso.aiff')
                    beepsad()
                    return

        if not os.path.exists(mount_point):
            beepsad()
            return

        try:
            mount_network_share(share, server_name, mount_point, fstype, user, password,auto_mount=False)
            beephappy()
            messagebox.showinfo("Mount", f"The mount for '{server_name}:{share}' to '{mount_point}' was successful.")
        except ValueError as e:
            beepsad()
            messagebox.showerror("Mount Error ValueError",f"{e}")
        except SystemError as e:
            beepsad()
            messagebox.showerror("Mount", f"The mount for '{server_name}:{share}' to '{mount_point}' failed with an error: {e}")            
        except Exception:
            beepsad()
            messagebox.showerror("Mount", f"The mount for '{server_name}:{share}' to '{mount_point}' failed with an error: {e}")





    

    def unmount(self):
        if selection := self.treeview.selection():
            item = self.treeview.item(selection) # type: ignore
            values = item["values"]
            share, server_name, user, password, mount_point, auto_mount, fstype = values

            if os.path.ismount(mount_point):
                unmount_command = f"umount {mount_point}"
                try:
                    subprocess.run(unmount_command, shell=True, check=True)
                    messagebox.showinfo("Unmount", f"The SMB unmount for '{share}' was successful.")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Unmount", f"The SMB unmount for '{share}' failed with error: {e}")
            else:
                    messagebox.showinfo("Mount", f"The directory '{mount_point}' is already dismounted.")    

        else:
            messagebox.showerror("Unmount", "Please select a mount to execute.")

    def clear_entries(self):
        self.share_entry.delete(0,  tk.END)
        self.server_entry.delete(0,  tk.END)
        self.user_entry.delete(0,  tk.END)
        self.password_entry.delete(0,  tk.END)
        self.mount_entry.delete(0,  tk.END)
        self.auto_mount_entry.delete(0,tk.END)
        self.fstype_entry.delete(0,tk.END)

    def load_mounts(self):
        self.treeview.delete(*self.treeview.get_children())  # Clear existing mounts

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                mounts = f.readlines()
            for mount in mounts:
                mount = mount.strip()
                share, server_name, user, password, mount_point, auto_mount, fstype = mount.split(",")
                #self.treeview.insert("", "end", text=str(i + 1),
                self.treeview.insert("", "end", values=(share, server_name, user, password, mount_point, auto_mount, fstype))
                if auto_mount == "A":
                   self.do_auto_mount(mount)
                   #self.do_auto_mount(values)


    def save_mounts(self):
        mounts = []
        line = ''
        
        for item in self.treeview.get_children():
            values = self.treeview.item(item)['values']
            line = ','.join(values)
            mounts.append(line)

        with open(file_path, "w") as f:
            f.write("\n".join(mounts))

    def get_column_names(self):
        return self["columns"]

    def test(self):
        column_names = []
        #column_names = self.get_column_names(self.treeview)
        #column_names = self.treeview["columns"]
        messagebox.showinfo("Column names", self.treeview["columns"])

    def save_on_exit(self):
        mounts = []
        self.save_mounts()
        root.destroy()
        quit()


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(True,True)

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "smbMounter.py" + '.txt')
    root.title(file_path)
    app = SmbManager(master=root)
    app.mainloop()

"""
rgranger,macmac,username,password,/Users/rgranger/mnt/macmac,M,SMB
media,freenas,username,password,/Users/rgranger/mnt/media,M,SMB
depot,freenas,username,password,/Users/rgranger/mnt/depot,M,SMB
/mnt/tank/vmprod/parallels/rmp2,freenas,username,password,/Users/rgranger/mnt/rmp2,A,NFS
"""
