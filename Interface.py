import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import airport


class AirportInterface:
    def __init__(self, root):
        # inici de marges i interface
        self.root = root
        self.root.title("airport management system")
        self.root.geometry("800x600")
        self.root.configure(bg="white")
        self.root.config(padx=20, pady=20, bg="white")

        self.airport_list = []

        # quadrat titol
        frame_header = tk.Frame(root, bg="white", height=80)
        frame_header.pack(fill="x", pady=10)
        frame_header.pack_propagate(False)  # prevents the frame from shrinking

        # load and place the eetac logo
        try:
            # load the logo image using the exact filename
            logo_image = Image.open('eetac.png')
            # resize the image to fit the header
            logo_image = logo_image.resize((120, 60), Image.Resampling.LANCZOS)
            # create a photolabel and place it on the left
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(frame_header, image=logo_photo, bg="white")
            logo_label.image = logo_photo  # keep a reference to avoid garbage collection
            # place the logo exactly on the left side
            logo_label.place(x=10, rely=0.5, anchor="w")
        except Exception as e:
            # silently pass if the logo is not found so the app still works
            pass

        # place the title label exactly in the center of the frame
        title_label = tk.Label(frame_header, text="AIRPORT MANAGEMENT SYSTEM", font=("helvetica", 18, "bold"),
                               bg="white", fg="black")
        title_label.place(relx=0.5, rely=0.5, anchor="center")

        # create top frame for basic loading and display operations, with white background
        frame_top = tk.Frame(root, bg="white")
        frame_top.pack(pady=5)
        # load and show buttons
        tk.Button(frame_top, text="Load airports", command=self.load_airports, width=20, bg="#add8e6", fg="black").grid(
            row=0, column=0, padx=5)
        tk.Button(frame_top, text="Show data", command=self.show_data, width=20, bg="#add8e6", fg="black").grid(row=0,
                                                                                                                column=1,
                                                                                                                padx=5)
        # set schengen button
        tk.Button(frame_top, text="Set schengen", command=self.set_schengen, width=20, bg="#d3d3d3", fg="black").grid(
            row=0, column=2, padx=5)

        # create middle frame for list modification operations, with white background
        frame_middle = tk.Frame(root, bg="white")
        frame_middle.pack(pady=5)
        # modification buttons
        tk.Button(frame_middle, text="Add airport", command=self.add_airport, width=20, bg="#f0e68c", fg="black").grid(
            row=0, column=0, padx=5)
        tk.Button(frame_middle, text="Delete airport", command=self.delete_airport, width=20, bg="#f0e68c",
                  fg="black").grid(row=0, column=1, padx=5)
        # save schengen button
        tk.Button(frame_middle, text="Save schengen", command=self.save_schengen, width=20, bg="#d3d3d3",
                  fg="black").grid(row=0, column=2, padx=5)

        # create bottom frame for graphical representations, with white background
        frame_bottom = tk.Frame(root, bg="white")
        frame_bottom.pack(pady=15)
        # graphical representation buttons
        tk.Button(frame_bottom, text="Plot schengen vs non-schengen", command=self.plot_airports, width=30,
                  bg="#90ee90", fg="black").grid(row=0, column=0, padx=5)
        tk.Button(frame_bottom, text="Show in google earth", command=self.show_map, width=30, bg="#90ee90",
                  fg="black").grid(row=0, column=1, padx=5)

        # create text area for console output simulation
        # removed anchor="w" to automatically center the text above the box
        tk.Label(root, text="Console output:", bg="white", fg="black").pack(pady=(10, 0))
        self.text_box = tk.Text(root, height=15, width=90, bg="white", fg="black", font=("consolas", 10))
        self.text_box.pack(pady=5)

    def write_console(self, message):
        # clear previous text and insert new message into the text box
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, message)

    def load_airports(self):
        # open file dialog to select airports text file
        try:
            filepath = filedialog.askopenfilename(title="select airports file", filetypes=[("text files", "*.txt")])
            if filepath:
                self.airport_list = airport.LoadAirports(filepath)
                self.write_console(f"successfully loaded {len(self.airport_list)} airports.")
                messagebox.showinfo("success", "airports loaded successfully.")
        except Exception as e:
            messagebox.showerror("error", f"could not load the file.\ndetails: {e}")

    def show_data(self):
        # display the loaded airports in the text box
        if not self.airport_list:
            messagebox.showwarning("warning", "please load airports first.")
            return

        display_text = ""
        for aero in self.airport_list:
            display_text += f"code: {aero.code:<4} \t| lat: {aero.latitude:<10.6f} | lon: {aero.longitude:<11.6f} \t | schengen: {aero.Schengen}\n"
        self.write_console(display_text)

    def set_schengen(self):
        # update schengen attribute for all airports in the list
        if not self.airport_list:
            messagebox.showwarning("warning", "no airports to update. please load them first.")
            return
        try:
            for aero in self.airport_list:
                airport.SetSchengen(aero)
            self.write_console("schengen attributes updated for all loaded airports.")
            messagebox.showinfo("success", "schengen attributes updated.")
        except Exception as e:
            messagebox.showerror("error", f"error updating schengen attributes: {e}")

    def add_airport(self):
        # prompt user for a new airport code and add it to the list
        code = simpledialog.askstring("new airport", "enter icao code (e.g., LEBL):")
        if not code: return

        try:
            new_aero = airport.Airport(code, [0.0, 0.0])
            airport.AddAirport(self.airport_list, new_aero)
            self.write_console(f"airport {code} successfully added.")
        except Exception as e:
            messagebox.showerror("error", f"error adding airport: {e}")

    def delete_airport(self):
        # prompt user for an airport code and remove it from the list
        code = simpledialog.askstring("delete airport", "enter icao code to delete:")
        if not code: return

        try:
            error = airport.RemoveAirport(self.airport_list, code)
            if error:
                messagebox.showerror("error", "airport not found in the list.")
            else:
                self.write_console(f"airport {code} removed from the list.")
        except Exception as e:
            messagebox.showerror("error", f"error deleting airport: {e}")

    def save_schengen(self):
        # save schengen airports to a new text file
        if not self.airport_list:
            messagebox.showwarning("warning", "no data to save.")
            return
        try:
            filepath = filedialog.asksaveasfilename(title="save as...", defaultextension=".txt")
            if filepath:
                airport.SaveSchengenAirports(self.airport_list, filepath)
                messagebox.showinfo("success", "file saved successfully.")
        except Exception as e:
            messagebox.showerror("error", f"error saving file: {e}")

    def plot_airports(self):
        # generate bar chart for schengen and non-schengen airports
        try:
            airport.PlotAirports(self.airport_list)
        except Exception as e:
            messagebox.showerror("error", f"could not generate plot.\nerror: {e}")

    def show_map(self):
        # generate google earth map for the loaded airports
        try:
            airport.MapAirports(self.airport_list)
        except Exception as e:
            messagebox.showerror("error", f"could not generate map.\nerror: {e}")


if __name__ == "__main__":
    # start the application loop
    root = tk.Tk()
    app = AirportInterface(root)
    root.mainloop()